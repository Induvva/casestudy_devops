
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Install dependencies') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''if ! python3 -m venv .venv; then
    echo "Python 3 is required on the Jenkins agent."
    exit 1
fi
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt'''
                    } else {
                        bat '''"C:\\Users\\duvva\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m venv .venv
if errorlevel 1 exit /b 1

.venv\\Scripts\\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 exit /b 1'''
                    }
                }
            }
        }

        stage('Validate Python syntax') {
            steps {
                script {
                    if (isUnix()) {
                        sh '.venv/bin/python -m compileall -q app.py db.py init_db.py add_admin_users.py apply_trip_feedback_migration.py check_feedback_schema.py'
                    } else {
                        bat '.venv\\Scripts\\python.exe -m compileall -q app.py db.py init_db.py add_admin_users.py apply_trip_feedback_migration.py check_feedback_schema.py'
                    }
                }
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker build -t tripplanner:v2 .'
                        sh 'docker run --rm tripplanner:v2 python -c "from pathlib import Path; assert not Path(\\\"/app/.env\\\").exists(), \\\".env must not be copied into the image\\\""'
                    } else {
                        bat 'docker build -t tripplanner:v2 .'
                        bat 'docker run --rm tripplanner:v2 python -c "from pathlib import Path; assert not Path(\'/app/.env\').exists(), \'.env must not be copied into the image\'"'
                    }
                }
            }
        }

        stage('Deploy to Docker Desktop Kubernetes') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
set -eu
context=$(kubectl config current-context)
if [ "$context" != "docker-desktop" ]; then
    echo "Expected the docker-desktop Kubernetes context; found: $context"
    exit 1
fi
kubectl get secret tripplanner-db
kubectl apply -f postgres.yaml
kubectl rollout status statefulset/tripplanner-postgres --timeout=180s
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
kubectl rollout restart deployment/tripplanner-deployment
kubectl rollout status deployment/tripplanner-deployment --timeout=180s
kubectl exec deployment/tripplanner-deployment -- python -c "from db import connect; c=connect(); q=c.cursor(); q.execute('SELECT current_database()'); db=q.fetchone()['current_database']; q.execute('SELECT * FROM users LIMIT 0'); print('PostgreSQL connection and users table verified:', db); c.close()"
'''
                    } else {
                        bat '''
@echo off
setlocal
for /f "delims=" %%C in ('kubectl config current-context') do set "KUBE_CONTEXT=%%C"
if not "%KUBE_CONTEXT%"=="docker-desktop" (
    echo Expected the docker-desktop Kubernetes context; found: %KUBE_CONTEXT%
    exit /b 1
)
kubectl get secret tripplanner-db
if errorlevel 1 exit /b 1
kubectl apply -f postgres.yaml
if errorlevel 1 exit /b 1
kubectl rollout status statefulset/tripplanner-postgres --timeout=180s
if errorlevel 1 exit /b 1
kubectl apply -f service.yaml
if errorlevel 1 exit /b 1
kubectl apply -f deployment.yaml
if errorlevel 1 exit /b 1
kubectl rollout restart deployment/tripplanner-deployment
if errorlevel 1 exit /b 1
kubectl rollout status deployment/tripplanner-deployment --timeout=180s
if errorlevel 1 exit /b 1
kubectl exec deployment/tripplanner-deployment -- python -c "from db import connect; c=connect(); q=c.cursor(); q.execute('SELECT current_database()'); db=q.fetchone()['current_database']; q.execute('SELECT * FROM users LIMIT 0'); print('PostgreSQL connection and users table verified:', db); c.close()"
if errorlevel 1 exit /b 1
'''
                    }
                }
            }
        }
    }
}
