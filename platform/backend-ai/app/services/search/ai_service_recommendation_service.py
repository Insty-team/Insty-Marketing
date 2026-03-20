from collections import defaultdict
from typing import List, Dict
from sqlalchemy.orm import Session
from openai import OpenAI
from pinecone import Pinecone
import requests
import json

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.repositories.course.course_repository import CourseRepository
from app.repositories.file.file_repository import FileRepository
from app.utils.prompt_loader import load_prompt
from app.utils.clean_gpt_text import enforce_html_breaks
from app.utils.s3_to_cloudfront_url import convert_s3_to_cloudfront_url
from app.utils.query_expander import expand_queries

settings = get_settings()
openai_client = OpenAI(api_key=settings.openai.api_key)
pinecone = Pinecone(api_key=settings.pinecone.api_key)
index = pinecone.Index(settings.pinecone.index_name)

SIMILARITY_THRESHOLD = 0.3
RRF_K = 60
MAX_EXPANSIONS = 5


class AIServiceRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoCourseRepository(db)
        self.course_repo = CourseRepository(self.db)
        self.file_repo = FileRepository(db)

    def recommend_ai_services_with_courses(
        self,
        query: str,
        top_k_services: int = 5,
        top_k_courses_per_service: int = 3
    ) -> dict:
        """
        1. 웹 검색으로 외부 AI 서비스 찾기
        2. 각 서비스별로 Pinecone에서 관련 강의 검색
        3. 결과 통합 및 메시지 생성
        """
        try:
            # 1. 외부 AI 서비스 검색
            external_services = self._search_external_ai_services(query, top_k_services)
            
            if not external_services:
                return {
                    "message": "관련된 AI 서비스를 찾을 수 없습니다.",
                    "services": []
                }
            
            # 2. 각 서비스별로 관련 강의 검색
            services_with_courses = []
            for service in external_services:
                related_courses = self._search_related_courses(
                    service_name=service["title"],
                    service_description=service["description"],
                    top_k=top_k_courses_per_service
                )
                
                services_with_courses.append({
                    "title": service["title"],
                    "url": service["url"],
                    "description": service["description"],
                    "type": "external_service",
                    "courses": related_courses
                })
            
            # 3. 통합 추천 메시지 생성
            message = self._generate_recommendation_message(
                query=query,
                services_with_courses=services_with_courses
            )
            
            return {
                "message": message,
                "services": services_with_courses
            }
            
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _translate_to_english(self, text: str) -> str:
        """한국어를 영어로 번역"""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a translator. Translate the given text to English. Only return the translated text, nothing else."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            translated = response.choices[0].message.content.strip()
            return translated
        except Exception as e:
            # 번역 실패 시 원본 반환
            return text

    def _search_external_ai_services(self, query: str, limit: int = 5) -> List[Dict]:
        """웹 검색으로 AI 서비스 찾기"""
        # 1. 영어로 번역
        english_query = self._translate_to_english(query)
        
        # 2. 검색 쿼리 개선 (공식 사이트/도구 강조)
        search_query = f"{english_query} official website tool service"
        
        params = {
            "q": search_query,
            "num": max(1, min(limit * 3, 15)),  # 더 많이 가져와서 필터링
            "engine": "google",
            "gl": "us",  # 북미 지역 검색
            "hl": "en",  # 영어 결과
            "api_key": settings.serpapi.api_key,
        }
        
        try:
            resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json() or {}
            organic = data.get("organic_results", []) or []
            
            # 1차 필터링: 블로그 도메인 제외
            blog_domains = [
                "medium.com", "tistory.com", "velog.io", "brunch.co.kr",
                "blog.naver.com", "blog.daum.net", "dev.to", "hashnode.com",
                "wordpress.com", "blogspot.com", "tumblr.com", "wixsite.com",
                "notion.so", "github.io", "substack.com"
            ]
            
            blog_keywords = ["blog", "tutorial", "guide", "how to", "review", "comparison", "article"]
            
            filtered_results = []
            for item in organic:
                url = item.get("link", "").lower()
                title = item.get("title", "").lower()
                snippet = item.get("snippet", "").lower()
                
                # 블로그 도메인 제외
                if any(domain in url for domain in blog_domains):
                    continue
                
                # 블로그 키워드가 제목에 포함된 경우 제외
                if any(keyword in title for keyword in blog_keywords):
                    continue
                
                # URL이 너무 깊은 경로인 경우 제외
                if any(path in url for path in ["/blog/", "/post/", "/article/", "/news/", "/tutorial/"]):
                    continue
                
                filtered_results.append({
                    "title": item.get("title") or "제목 없음",
                    "url": item.get("link") or "",
                    "description": item.get("snippet") or "",
                })
            
            # 2차 필터링: GPT로 실제 서비스인지 판단
            if filtered_results:
                services = self._filter_ai_services_with_gpt(filtered_results, limit)
                return services
            
            return []
        except Exception as e:
            # 웹 검색 실패 시 빈 리스트 반환
            return []

    def _filter_ai_services_with_gpt(self, results: List[Dict], limit: int) -> List[Dict]:
        """GPT를 사용해서 실제 AI 서비스인지 필터링"""
        try:
            # 검색 결과를 JSON 형식으로 정리
            results_json = json.dumps(results, ensure_ascii=False, indent=2)
            
            prompt = f"""You are a filter that identifies real AI service/tool official websites from web search results.

Exclude:
- Blog posts, tutorials, guides, reviews, news articles
- GitHub repositories (unless it's the official service page)
- Documentation pages (unless it's the main service page)
- Comparison articles or "best of" lists

Include only:
- Official websites of AI services/tools
- Main product pages
- Service landing pages

Search results:
{results_json}

Return a JSON array with only the official AI service websites. Format:
[
  {{
    "title": "Service Title",
    "url": "Service URL",
    "description": "Service Description"
  }}
]

Return ONLY the JSON array, no code blocks, no explanations."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            raw = response.choices[0].message.content.strip()
            # JSON 블럭 제거
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            
            filtered = json.loads(raw)
            return filtered[:limit]
            
        except Exception as e:
            # GPT 필터링 실패 시 원본 결과 반환 (상위 limit개만)
            return results[:limit]

    def _search_related_courses(
        self,
        service_name: str,
        service_description: str,
        top_k: int = 3
    ) -> List[dict]:
        """서비스별로 관련 강의 검색 (Pinecone)"""
        # 검색 쿼리 생성
        search_query = f"{service_name} {service_description}"
        
        # 질의 확장
        expanded = expand_queries(search_query, n=MAX_EXPANSIONS)
        all_queries = [search_query] + [
            q for q in expanded 
            if q.strip().lower() != search_query.strip().lower()
        ]
        
        # 배치 임베딩
        query_vectors = self._embed_queries(all_queries)
        
        # RRF 점수 결합
        rrf_scores = defaultdict(float)
        video_texts = {}
        
        per_query_k = max(1, 20 // len(all_queries))
        
        for q_vec in query_vectors:
            resp = index.query(
                vector=q_vec,
                top_k=per_query_k,
                include_metadata=True
            )
            
            for rank, match in enumerate(resp.get("matches", []), start=1):
                metadata = match.get("metadata") or {}
                score = match.get("score", 0.0)
                
                vid_raw = metadata.get("video_id")
                try:
                    vid = int(vid_raw)
                except (ValueError, TypeError):
                    continue
                
                chunk_text = metadata.get("text")
                if not chunk_text or score < SIMILARITY_THRESHOLD:
                    continue
                
                rrf_scores[vid] += 1.0 / (RRF_K + rank)
                if vid not in video_texts:
                    video_texts[vid] = chunk_text
        
        if not rrf_scores:
            return []
        
        # 상위 강의 선택
        sorted_video_scores = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_video_ids = [int(vid) for vid, _ in sorted_video_scores[:top_k]]
        
        # 강의 정보 조회
        video_objs = self.video_repo.get_by_video_ids(top_video_ids)
        
        # video.id -> course.id 매핑
        video_id_to_course_id: dict[int, int] = {}
        for video in video_objs:
            course_id = getattr(video, "course_id", None)
            if course_id is None and getattr(video, "course", None) is not None:
                course_id = getattr(video.course, "id", None)
            if course_id is None:
                continue
            video_id_to_course_id[video.id] = int(course_id)
        
        # course_id 있는 video만 필터
        filtered_top_video_ids = [
            vid for vid in top_video_ids
            if vid in video_id_to_course_id
        ]
        
        if not filtered_top_video_ids:
            return []
        
        # 강의 정보 일괄 조회
        course_ids = list(set(video_id_to_course_id.values()))
        course_objs = self.course_repo.get_by_ids(course_ids)
        course_id_to_title = {
            course.id: course.title
            for course in course_objs
        }
        
        video_dict = {
            video.id: video
            for video in video_objs
            if video.id in video_id_to_course_id
        }
        
        courses = []
        for vid in filtered_top_video_ids:
            video = video_dict.get(vid)
            if not video:
                continue
            
            course_id = video_id_to_course_id[vid]
            
            # 썸네일 URL 조회
            status, video_uuid = self.course_repo.get_thumbnail_status(course_id)
            thumbnail_url = None
            
            if status == "custom":
                file = self.file_repo.get_course_thumbnail_by_course_id(course_id)
                if file and file.name:
                    thumbnail_url = convert_s3_to_cloudfront_url(
                        f"/file/COURSE_THUMBNAIL/{file.container_id}/{file.name}"
                    )
            elif status == "default" and video_uuid:
                thumbnail_url = convert_s3_to_cloudfront_url(
                    f"/file/VIDEO_BASIC_THUMBNAIL/{video_uuid}/basic_thumbnail.jpg"
                )
            
            courses.append({
                "course_id": str(course_id),
                "course_title": course_id_to_title.get(course_id, "제목 없음"),
                "thumbnail_url": thumbnail_url
            })
        
        return courses

    def _embed_queries(self, queries: List[str]) -> List[List[float]]:
        """배치 임베딩"""
        try:
            resp = openai_client.embeddings.create(
                input=queries,
                model="text-embedding-3-large"
            )
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _generate_recommendation_message(
        self,
        query: str,
        services_with_courses: List[dict]
    ) -> str:
        """통합 추천 메시지 생성"""
        try:
            prompt = load_prompt("ai_service_recommendation_prompt.j2", {
                "query": query,
                "services": services_with_courses
            })
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw = response.choices[0].message.content.strip()
            return enforce_html_breaks(raw)
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
