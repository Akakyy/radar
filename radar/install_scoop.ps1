Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
iex "& {$(irm get.scoop.sh)} -RunAsAdmin"
scoop install ffmpeg