pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test Pipeline') {
            steps {
                sh 'bash scripts/test.sh'
            }
        }
    }

    post {
        success {
            echo 'Jenkins pipeline completed successfully!'
        }
        failure {
            echo 'Jenkins pipeline failed!'
        }
    }
}