pipeline {
    agent { label 'docker' }

    environment {
        DOCKER_BUILDKIT = '1'
        OUTPUT_ISO = 'multiboot-usb-live.iso'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m pip install -e ".[dev]"
                    python3 -m pytest tests/ -v --tb=short
                '''
            }
        }

        stage('Build ISO') {
            steps {
                sh 'bash deploy/build-iso.sh'
            }
        }

        stage('Verify ISO') {
            steps {
                sh '''
                    # Verify ISO is bootable
                    file ${OUTPUT_ISO}
                    # Check ISO size (should be > 100MB)
                    SIZE=$(stat -c%s ${OUTPUT_ISO})
                    if [ "$SIZE" -lt 104857600 ]; then
                        echo "ERROR: ISO too small ($SIZE bytes)"
                        exit 1
                    fi
                    echo "ISO verified: ${SIZE} bytes"
                '''
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: "${OUTPUT_ISO}", fingerprint: true, onlyIfSuccessful: true
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            echo 'Build failed! Check logs.'
        }
        success {
            echo "ISO built successfully: ${OUTPUT_ISO}"
        }
    }
}
