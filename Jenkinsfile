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
                        sh '''python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt'''
                    } else {
                        bat '''py -3 -m venv .venv
.venv\\Scripts\\python.exe -m pip install --disable-pip-version-check -r requirements.txt'''
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
