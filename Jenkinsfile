pipeline {
  agent { label 'docker-python-kubectl' }
  options { timestamps(); disableConcurrentBuilds(); timeout(time: 30, unit: 'MINUTES') }
  environment {
    IMAGE_REPO = 'ghcr.io/REPLACE_ORG/intelligent-calculator-api'
    KUBE_NAMESPACE = 'calculator-staging'
  }
  stages {
    stage('Checkout') { steps { checkout scm; script { env.SHORT_SHA = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim() } } }
    stage('Install & test') { steps { sh 'python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/ruff check app tests && .venv/bin/pytest -q --junitxml=test-results.xml' } post { always { junit allowEmptyResults: true, testResults: 'test-results.xml' } } }
    stage('Dependency audit') { steps { sh '.venv/bin/pip-audit --progress-spinner off' } }
    stage('Build image') { steps { sh 'docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t "$IMAGE_REPO:$SHORT_SHA" .' } }
    stage('Container scan') { steps { sh 'trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed "$IMAGE_REPO:$SHORT_SHA"' } }
    stage('Publish') {
      when { branch 'main' }
      steps { withCredentials([usernamePassword(credentialsId: 'ghcr-push', usernameVariable: 'REG_USER', passwordVariable: 'REG_TOKEN')]) {
        sh 'echo "$REG_TOKEN" | docker login ghcr.io -u "$REG_USER" --password-stdin && docker push "$IMAGE_REPO:$SHORT_SHA" && docker logout ghcr.io'
      } }
    }
    stage('Deploy staging') {
      when { branch 'main' }
      steps { withCredentials([file(credentialsId:'calculator-kubeconfig',variable:'KUBECONFIG')]) {
        sh 'kubectl -n "$KUBE_NAMESPACE" set image deployment/calculator-api api="$IMAGE_REPO:$SHORT_SHA" && kubectl -n "$KUBE_NAMESPACE" rollout status deployment/calculator-api --timeout=180s'
      } }
    }
    stage('Smoke test') {
      when { branch 'main' }
      steps { sh 'test -n "$STAGING_API_URL" && curl --fail --silent --show-error "$STAGING_API_URL/health/ready" && curl --fail --silent --show-error "$STAGING_API_URL/api/v1/version"' }
    }
  }
  post {
    failure { echo 'Deployment or validation failed. Review the rollout and run the documented rollback workflow.' }
    always { archiveArtifacts allowEmptyArchive:true, artifacts:'test-results.xml' }
  }
}
