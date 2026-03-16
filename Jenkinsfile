// Jenkins Declarative Pipeline
pipeline {

    // Run the pipeline on any available Jenkins agent/node
    agent any

    stages {

        // ---------------------------------------------------------
        // Stage 1: Checkout Code
        // ---------------------------------------------------------
        stage('Checkout Code') {
            steps {
                // This pulls the source code from the Git repository
                // that is configured in the Jenkins job
                checkout scm
            }
        }

        // ---------------------------------------------------------
        // Stage 2: Validate Python Code
        // ---------------------------------------------------------
        stage('Validate Python Code') {

            // Run this stage inside a Python Docker container
            // so the Jenkins machine doesn't need Python installed
            agent {
                docker {
                    image 'python:3.11'
                }
            }

            steps {
                // py_compile checks Python syntax errors
                // If the DAG file has syntax issues, the pipeline fails here
                sh 'python -m py_compile airflow/Dags/payment_pipeline_dag.py'
            }
        }

        // ---------------------------------------------------------
        // Stage 3: Install Dependencies
        // ---------------------------------------------------------
        stage('Install Dependencies') {

            // Again using a Python Docker container
            agent {
                docker {
                    image 'python:3.11'
                }
            }

            steps {
                // Install required Python libraries
                // defined in requirements.txt
                sh 'pip install -r requirements.txt'
            }
        }

        // ---------------------------------------------------------
        // Stage 4: Build Docker Images
        // ---------------------------------------------------------
        stage('Build Docker Images') {
            steps {

                // Builds all Docker services defined in docker-compose.yml
                // Example services in your project:
                // - Kafka
                // - Zookeeper
                // - Flink
                // - Postgres
                // - Airflow
                sh 'docker-compose build'
            }
        }

        // ---------------------------------------------------------
        // Stage 5: Deploy Data Platform
        // ---------------------------------------------------------
        stage('Deploy Data Platform') {
            steps {

                // Starts all containers in detached mode (-d)
                // This launches the entire streaming platform stack
                // defined in docker-compose.yml
                sh 'docker-compose up -d'
            }
        }

        // ---------------------------------------------------------
        // Stage 6: Health Check
        // ---------------------------------------------------------
        stage('Health Check') {
            steps {

                // Lists running containers to verify
                // the services started successfully
                sh 'docker ps'
            }
        }
    }

    // ---------------------------------------------------------
    // Post Pipeline Actions
    // ---------------------------------------------------------
    post {

        // If any stage fails, Jenkins executes this block
        failure {

            // Simple message for debugging/logging
            echo 'Pipeline failed!'
        }
    }
}