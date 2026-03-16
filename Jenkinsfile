// Jenkins Declarative Pipeline Definition
pipeline {

    // --------------------------------------------------
    // Agent Configuration
    // --------------------------------------------------
    agent {
        docker {
            // Run the entire pipeline inside a Docker container
            // This ensures a consistent environment for builds
            image 'python:3.11'

            // Run container as root user
            // Required when installing packages or running Docker commands
            args '-u root'
        }
    }

    // --------------------------------------------------
    // Pipeline Stages
    // Each stage represents a logical step in the CI/CD workflow
    // --------------------------------------------------
    stages {

        // --------------------------------------------------
        // Stage 1: Checkout Code
        // --------------------------------------------------
        stage('Checkout Code') {
            steps {
                // Pull the latest code from the Git repository
                // Jenkins automatically uses the repo configured in the job
                checkout scm
            }
        }

        // --------------------------------------------------
        // Stage 2: Validate Python Code
        // --------------------------------------------------
        stage('Validate Python Code') {
            steps {
                // Compile the Python DAG file to check for syntax errors
                // This does NOT run the code — it only validates syntax
                sh 'python -m py_compile airflow/Dags/payment_pipeline_dag.py'
            }
        }

        // --------------------------------------------------
        // Stage 3: Install Dependencies
        // --------------------------------------------------
        stage('Install Dependencies') {
            steps {
                // Install Python libraries required by the project
                // dependencies are listed inside requirements.txt
                sh 'pip install -r requirements.txt'
            }
        }

        // --------------------------------------------------
        // Stage 4: Build Docker Images
        // --------------------------------------------------
        stage('Build Docker Images') {
            steps {
                // Build all Docker images defined in docker-compose.yml
                // Example services: kafka, flink, postgres, airflow, etc.
                sh 'docker compose build'
            }
        }

        // --------------------------------------------------
        // Stage 5: Deploy Data Platform
        // --------------------------------------------------
        stage('Deploy Data Platform') {
            steps {
                // Start all services in detached mode (-d)
                // Docker Compose will start containers like:
                // Kafka, Zookeeper, Flink, PostgreSQL, Grafana, Prometheus
                sh 'docker compose up -d'
            }
        }

        // --------------------------------------------------
        // Stage 6: Health Check
        // --------------------------------------------------
        stage('Health Check') {
            steps {
                // Display running Docker containers
                // Helps confirm if services started successfully
                sh 'docker ps'
            }
        }
    }

    // --------------------------------------------------
    // Post Pipeline Actions
    // Runs after the pipeline completes
    // --------------------------------------------------
    post {

        // If any stage fails
        failure {
            // Print failure message in Jenkins console
            echo 'Pipeline failed!'
        }

        // If pipeline completes successfully
        success {
            // Print success message in Jenkins console
            echo 'Pipeline succeeded!'
        }
    }
}