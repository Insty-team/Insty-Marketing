#!/usr/bin/env sh
if [ -z "$husky_skip_init" ]; then
  readonly hook_name="$(basename -- "$0")"
  echo "🚀 Husky(Start) - 시작된 훅 이름 : $hook_name"

  readonly husky_skip_init=1
  export husky_skip_init

  sh "$0" "$@"
  exitCode="$?"

  if [ $exitCode -ne 0 ]; then
    echo "❌ Husky(Error), 이름:{$hook_name} 에러코드:{$exitCode}"
  fi

  echo "✅ Husky(Success) - 완료된 훅 이름 : $hook_name"
  exit $exitCode
fi