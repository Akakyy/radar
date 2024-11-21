Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
iex "& {$(irm get.scoop.sh)} -RunAsAdmin"
scoop install ffmpeg



python -m deeppavlov download ner_rus_bert
set DEEPPAVLOV_HOME=/path/to/your/custom/directory
