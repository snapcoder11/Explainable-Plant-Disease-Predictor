document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const uploadContent = document.getElementById('upload-content');
    const imagePreview = document.getElementById('image-preview');
    const predictBtn = document.getElementById('predict-btn');
    const loadingOverlay = document.getElementById('loading');
    const resultsSection = document.getElementById('results-section');
    const diseaseNameEl = document.getElementById('disease-name');
    const confidenceBarFill = document.getElementById('confidence-bar');
    const confidenceText = document.getElementById('confidence-text');
    
    let currentFile = null;
    let conceptChart = null;

    // Handle Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    // Handle Click to Upload
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                currentFile = file;
                previewFile(file);
                predictBtn.disabled = false;
                // hide results if a new file is added
                resultsSection.classList.add('hidden');
            } else {
                alert('Please upload an image file.');
            }
        }
    }

    function previewFile(file) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = function() {
            imagePreview.src = reader.result;
            imagePreview.classList.remove('hidden');
            uploadContent.classList.add('hidden');
        }
    }

    // Prediction
    predictBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        // Show loading state
        loadingOverlay.classList.remove('hidden');
        predictBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Network response was not ok. Status: ' + response.status);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error during prediction:', error);
            alert('An error occurred during prediction. Please try again.');
        } finally {
            loadingOverlay.classList.add('hidden');
            predictBtn.disabled = false;
        }
    });

    function displayResults(data) {
        const { predicted_class, confidence, concepts } = data;

        // Update Text
        diseaseNameEl.textContent = predicted_class;
        
        // Update Confidence Bar
        const confidencePercentage = (confidence * 100).toFixed(1);
        setTimeout(() => {
            confidenceBarFill.style.width = `${confidencePercentage}%`;
        }, 100);
        confidenceText.textContent = `${confidencePercentage}%`;

        // Adjust bar color based on confidence
        if (confidence > 0.8) {
            confidenceBarFill.style.background = 'linear-gradient(90deg, #34d399, #10b981)';
        } else if (confidence > 0.5) {
            confidenceBarFill.style.background = 'linear-gradient(90deg, #fbbf24, #f59e0b)';
        } else {
            confidenceBarFill.style.background = 'linear-gradient(90deg, #f87171, #ef4444)';
        }

        // Show results section
        resultsSection.classList.remove('hidden');
        
        // Scroll to results smoothly
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        renderChart(concepts);
    }

    function renderChart(concepts) {
        const ctx = document.getElementById('concept-chart').getContext('2d');
        
        const labels = concepts.map(c => c.name);
        const scores = concepts.map(c => c.score);
        
        // Generate dynamic colors based on score
        const backgroundColors = scores.map(score => {
            if (score > 0.7) return 'rgba(16, 185, 129, 0.8)'; // Green
            if (score > 0.4) return 'rgba(245, 158, 11, 0.8)'; // Yellow/Orange
            return 'rgba(239, 68, 68, 0.8)'; // Red
        });

        if (conceptChart) {
            conceptChart.destroy();
        }

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

        conceptChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Concept Activation Score',
                    data: scores,
                    backgroundColor: backgroundColors,
                    borderRadius: 4,
                    borderWidth: 1,
                    borderColor: 'rgba(255, 255, 255, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `Score: ${context.parsed.y.toFixed(3)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.1,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            stepSize: 0.2
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }
});
