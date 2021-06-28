docker build -t too-good-to-go-cloud-notifier .
docker tag too-good-to-go-cloud-notifier:latest 166718199143.dkr.ecr.eu-central-1.amazonaws.com/too-good-to-go-cloud-notifier:latest
aws ecr get-login-password --profile Personal | docker login --username AWS --password-stdin 166718199143.dkr.ecr.eu-central-1.amazonaws.com/too-good-to-go-cloud-notifier 
docker push 166718199143.dkr.ecr.eu-central-1.amazonaws.com/too-good-to-go-cloud-notifier
aws ecs update-service --cluster grpc --service too-good-to-go-cloud-notifier --force-new-deployment --profile Personal
docker image prune -f