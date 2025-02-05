#!/bin/bash
set -e
HOST='13.55.250.149'
PROJECT='staging'

echo -e "\n>>> Copying staging compose file to clerk at $HOST"
scp -o StrictHostKeyChecking=no  docker/docker-compose.staging.yml root@${HOST}:/srv/clerk_test/


echo -e "\n>>> SSHing into clerk at $HOST."
ssh -o StrictHostKeyChecking=no root@$HOST /bin/bash << EOF
    set -e
    cd /srv/clerk_test/
    docker pull anikalaw/clerk:staging
    docker-compose \
        -p task \
        -f docker-compose.staging.yml \
        run --rm web \
        /app/scripts/tasks/staging-sync.sh
EOF
echo -e "\n>>> Deployment finished for $PROJECT"
