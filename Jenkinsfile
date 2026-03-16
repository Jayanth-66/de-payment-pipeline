pipeline {

    // Jenkins can run this pipeline on any available agent/node
    agent any

    stages {

        // -------------------------------------------------------
        // Stage 1: Checkout Code from Git Repository
        // -------------------------------------------------------
        stage('Checkout Code') {
            steps {
                // Pulls the latest code from the configured SCM
                // (GitHub / GitLab / Bitbucket etc.)
                checkout scm
            }
        }

        // -------------------------------------------------------
        // Stage 2: Validate Python Code
        // -------------------------------------------------------
        stage('Validate Python Code') {
            steps {
                sh '''
                # Check Python syntax without executing the files
                # This helps detect syntax errors early

                python -m py_compile airflow/Dags/payment_pipeline_dag.py
                python -m py_compile flink-job/PaymentStreamProcessor.py
                '''
            }
        }

        // -------------------------------------------------------
        // Stage 3: Install Python Dependencies
        // -------------------------------------------------------
        stage('Install Dependencies') {
            steps {
                sh '''
                # Install all required Python packages listed
                # in requirements.txt for the project

                pip install -r requirements.txt
                '''
            }
        }

        // -------------------------------------------------------
        // Stage 4: Build Docker Images
        // -------------------------------------------------------
        stage('Build Docker Images') {
            steps {
                sh '''
                # Build all services defined in docker-compose.yml
                # This includes Kafka, Flink, Airflow, PostgreSQL,
                # Prometheus, Grafana etc.

                docker compose build
                '''
            }
        }

        // -------------------------------------------------------
        // Stage 5: Deploy Data Platform
        // -------------------------------------------------------
        stage('Deploy Data Platform') {
            steps {
                sh '''
                # Start all containers in detached mode
                # This launches the full streaming platform

                docker compose up -d
                '''
            }
        }

        // -------------------------------------------------------
        // Stage 6: Health Check
        // -------------------------------------------------------
        stage('Health Check') {
            steps {
                sh '''
                # Verify that important services are running

                # Check Airflow health endpoint
                curl -f http://localhost:8088/health

                # Check Prometheus health endpoint
                curl -f http://localhost:9090/-/healthy
                '''
            }
        }

    }

    // -------------------------------------------------------
    // Post Actions
    // -------------------------------------------------------
    post {

        // If pipeline succeeds
        success {
            echo 'Pipeline deployed successfully!'
        }

        // If pipeline fails
        failure {
            echo 'Pipeline failed!'
        }
    }
}