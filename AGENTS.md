# Agent Instructions

[git]
- 사용자 요청 작업이 완료되면 `idghst-git-commit-push-korean`(`/Users/idghst/.codex/skills/idghst-git-commit-push-korean/SKILL.md`)을 바로 실행한다.
- 이번 세션에서 만든 변경만 한글 제목으로 커밋하고 현재 브랜치를 `git push`한다.
- `.env`, credentials, token, 비밀값, 이번 작업과 무관한 dirty 파일은 제외하고 남은 파일은 보고한다.
- force push, 자동 pull/rebase/merge, `--no-verify`는 명시 요청 없이 하지 않는다.
- 커밋할 변경이 없으면 커밋하지 않는다.
