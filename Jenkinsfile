
pipeline {
    agent any

    options {
        timestamps()
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
                        sh '.venv/bin/python -m compileall -q app.py init_db.py add_admin_users.py apply_trip_feedback_migration.py check_feedback_schema.py'
                    } else {
                        bat '.venv\\Scripts\\python.exe -m compileall -q app.py init_db.py add_admin_users.py apply_trip_feedback_migration.py check_feedback_schema.py'
                    }
                }
            }
        }
    }
}
