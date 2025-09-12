/**
 * Heatmap Dashboard JavaScript
 * Interactive visualization and real-time updates for collaboration heatmap
 */

class HeatmapDashboard {
    constructor() {
        this.currentQuizId = null;
        this.currentView = 'clicks';
        this.refreshInterval = 10000; // 10 seconds
        this.autoRefreshTimer = null;
        this.engagementChart = null;
        this.insights = [];
        this.heatmapData = {};
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Real-time updates
        this.startAutoRefresh();
        
        // Window focus/blur events for pausing updates
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });
    }
    
    async loadQuizHeatmap() {
        const quizSelect = document.getElementById('quizSelect');
        const quizId = quizSelect.value;
        
        if (!quizId) {
            document.getElementById('heatmapContent').classList.add('d-none');
            return;
        }
        
        this.currentQuizId = quizId;
        document.getElementById('heatmapContent').classList.remove('d-none');
        
        // Show loading state
        this.showLoadingState();
        
        try {
            // Load heatmap data and insights simultaneously
            const [heatmapResponse, insightsResponse] = await Promise.all([
                fetch(`/api/heatmap/data/${quizId}`),
                fetch(`/api/heatmap/insights/${quizId}`)
            ]);
            
            const heatmapData = await heatmapResponse.json();
            const insightsData = await insightsResponse.json();
            
            if (heatmapData.success) {
                this.heatmapData = heatmapData;
                this.renderHeatmapVisualization(heatmapData);
                this.updateMetricsOverview(heatmapData);
                this.renderQuestionAnalysisTable(heatmapData);
                this.renderEngagementChart(heatmapData);
            }
            
            if (insightsData.success) {
                this.insights = insightsData.insights;
                this.renderInsights(insightsData);
            }
            
        } catch (error) {
            console.error('Error loading heatmap data:', error);
            this.showErrorState('Failed to load heatmap data. Please try again.');
        }
    }
    
    renderHeatmapVisualization(data) {
        const container = document.getElementById('questionsHeatmap');
        container.innerHTML = '';
        
        if (!data.questionsData || data.questionsData.length === 0) {
            container.innerHTML = `
                <div class="text-center text-white-50 py-5">
                    <i class="fas fa-chart-bar fa-3x mb-3"></i>
                    <p>No interaction data available yet</p>
                    <small>Data will appear as participants interact with the quiz</small>
                </div>
            `;
            return;
        }
        
        data.questionsData.forEach((questionData, index) => {
            const questionElement = this.createQuestionHeatmap(questionData, index + 1);
            container.appendChild(questionElement);
        });
        
        // Update view buttons
        this.updateViewButtons();
    }
    
    createQuestionHeatmap(questionData, questionNumber) {
        const element = document.createElement('div');
        element.className = 'heatmap-question';
        
        const difficulty = this.calculateDifficulty(questionData.correctAnswerRate);
        const hotspots = this.currentView === 'clicks' ? questionData.clickHotspots : questionData.hoverHotspots;
        
        element.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h6 class="text-white mb-1">Question ${questionNumber}</h6>
                    <span class="difficulty-indicator difficulty-${difficulty.level}">
                        ${difficulty.label}
                    </span>
                </div>
                <div class="text-white-50 small">
                    <div><i class="fas fa-users me-1"></i>${questionData.totalParticipants} participants</div>
                    <div><i class="fas fa-clock me-1"></i>${questionData.averageTimeSpent?.toFixed(1) || 0}s avg</div>
                </div>
            </div>
            
            <div class="heatmap-canvas" id="heatmap-${questionData.questionId}">
                <div class="hotspot-overlay" id="hotspots-${questionData.questionId}">
                    ${this.renderHotspots(hotspots)}
                </div>
                <div class="p-3 text-center">
                    <div class="row text-dark">
                        <div class="col-3">
                            <div class="h4 mb-1">${questionData.totalClicks}</div>
                            <small>Clicks</small>
                        </div>
                        <div class="col-3">
                            <div class="h4 mb-1">${questionData.totalHovers}</div>
                            <small>Hovers</small>
                        </div>
                        <div class="col-3">
                            <div class="h4 mb-1">${questionData.correctAnswerRate?.toFixed(1) || 0}%</div>
                            <small>Accuracy</small>
                        </div>
                        <div class="col-3">
                            <div class="h4 mb-1">${questionData.engagementScore?.toFixed(1) || 0}</div>
                            <small>Engagement</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-2 d-flex justify-content-end">
                <button class="btn btn-sm btn-outline-light" onclick="showQuestionDetails(${questionData.questionId})">
                    <i class="fas fa-eye me-1"></i>View Details
                </button>
            </div>
        `;
        
        return element;
    }
    
    renderHotspots(hotspots) {
        if (!hotspots || hotspots.length === 0) {
            return '';
        }
        
        return hotspots.slice(0, 20).map(([x, y]) => {
            if (x === null || y === null) return '';
            
            const size = 20 + Math.random() * 15; // Varying sizes
            const left = Math.max(0, Math.min(95, (x / 1000) * 100)); // Normalize to percentage
            const top = Math.max(0, Math.min(95, (y / 600) * 100)); // Normalize to percentage
            
            return `
                <div class="hotspot-point" style="
                    left: ${left}%; 
                    top: ${top}%; 
                    width: ${size}px; 
                    height: ${size}px;
                    animation-delay: ${Math.random() * 2}s;
                "></div>
            `;
        }).join('');
    }
    
    calculateDifficulty(correctRate) {
        if (correctRate >= 80) return { level: 'easy', label: 'Easy' };
        if (correctRate >= 60) return { level: 'medium', label: 'Medium' };
        return { level: 'hard', label: 'Hard' };
    }
    
    updateMetricsOverview(data) {
        const totalParticipants = Math.max(...data.questionsData.map(q => q.totalParticipants || 0));
        const avgEngagement = data.questionsData.length > 0 
            ? data.questionsData.reduce((sum, q) => sum + (q.engagementScore || 0), 0) / data.questionsData.length 
            : 0;
        const difficultQuestions = data.questionsData.filter(q => (q.correctAnswerRate || 0) < 60).length;
        
        document.getElementById('totalParticipants').textContent = totalParticipants;
        document.getElementById('avgEngagement').textContent = `${avgEngagement.toFixed(1)}%`;
        document.getElementById('difficultQuestions').textContent = difficultQuestions;
        document.getElementById('activeInsights').textContent = this.insights.length;
    }
    
    renderInsights(data) {
        const container = document.getElementById('insightsContainer');
        
        if (!data.insights || data.insights.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-check-circle fa-2x mb-3 text-success"></i>
                    <p>No insights generated yet</p>
                    <small>Insights will appear as more data becomes available</small>
                </div>
            `;
            return;
        }
        
        container.innerHTML = data.insights.map(insight => `
            <div class="insight-card insight-${insight.severity} card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-1">
                            <i class="fas fa-${this.getInsightIcon(insight.type)} me-2"></i>
                            ${insight.title}
                        </h6>
                        <span class="badge bg-${this.getSeverityColor(insight.severity)}">${insight.severity.toUpperCase()}</span>
                    </div>
                    <p class="card-text small text-muted">${insight.description}</p>
                    ${insight.suggestedActions.length > 0 ? `
                        <div class="mt-2">
                            <strong class="small">Suggested Actions:</strong>
                            <ul class="small mb-2">
                                ${insight.suggestedActions.slice(0, 2).map(action => `<li>${action}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            ${new Date(insight.createdAt).toLocaleString()}
                        </small>
                        ${!insight.isAcknowledged ? `
                            <button class="btn btn-sm btn-outline-primary" onclick="acknowledgeInsight(${insight.id})">
                                <i class="fas fa-check me-1"></i>Acknowledge
                            </button>
                        ` : '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Acknowledged</small>'}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    renderQuestionAnalysisTable(data) {
        const tbody = document.querySelector('#questionAnalysisTable tbody');
        
        if (!data.questionsData || data.questionsData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-table fa-2x mb-2"></i><br>
                        No question data available
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = data.questionsData.map((q, index) => {
            const difficulty = this.calculateDifficulty(q.correctAnswerRate || 0);
            return `
                <tr>
                    <td>
                        <strong>Question ${index + 1}</strong>
                        <br><small class="text-muted">ID: ${q.questionId}</small>
                    </td>
                    <td>
                        <span class="difficulty-indicator difficulty-${difficulty.level}">
                            ${difficulty.label}
                        </span>
                    </td>
                    <td>${q.totalParticipants || 0}</td>
                    <td>${(q.averageTimeSpent || 0).toFixed(1)}s</td>
                    <td>
                        <div class="progress" style="height: 8px;">
                            <div class="progress-bar bg-${(q.correctAnswerRate || 0) >= 80 ? 'success' : (q.correctAnswerRate || 0) >= 60 ? 'warning' : 'danger'}" 
                                 style="width: ${q.correctAnswerRate || 0}%"></div>
                        </div>
                        <small>${(q.correctAnswerRate || 0).toFixed(1)}%</small>
                    </td>
                    <td>${(q.engagementScore || 0).toFixed(1)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="showQuestionDetails(${q.questionId})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    renderEngagementChart(data) {
        const ctx = document.getElementById('engagementChart');
        
        if (this.engagementChart) {
            this.engagementChart.destroy();
        }
        
        // Simulate engagement timeline data
        const timeLabels = [];
        const engagementValues = [];
        
        for (let i = 0; i < 20; i++) {
            timeLabels.push(new Date(Date.now() - (19 - i) * 60000).toLocaleTimeString());
            engagementValues.push(Math.random() * 100);
        }
        
        this.engagementChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'Engagement Score',
                    data: engagementValues,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    setHeatmapView(view) {
        this.currentView = view;
        this.updateViewButtons();
        
        if (this.currentQuizId) {
            this.renderHeatmapVisualization(this.heatmapData);
        }
    }
    
    updateViewButtons() {
        ['clicks', 'hovers', 'time'].forEach(view => {
            const btn = document.getElementById(`${view}Btn`);
            if (btn) {
                btn.classList.toggle('active', view === this.currentView);
            }
        });
    }
    
    getInsightIcon(type) {
        const icons = {
            'difficulty_pattern': 'exclamation-triangle',
            'engagement_drop': 'arrow-down',
            'confusion_area': 'question-circle',
            'performance_trend': 'chart-line',
            'interaction_hotspot': 'map-marker-alt'
        };
        return icons[type] || 'info-circle';
    }
    
    getSeverityColor(severity) {
        const colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'success'
        };
        return colors[severity] || 'secondary';
    }
    
    showLoadingState() {
        document.getElementById('questionsHeatmap').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-white mt-3">Loading heatmap data...</p>
            </div>
        `;
        
        document.getElementById('insightsContainer').innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Analyzing insights...</p>
            </div>
        `;
    }
    
    showErrorState(message) {
        document.getElementById('questionsHeatmap').innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-warning fa-3x mb-3"></i>
                <p class="text-white">${message}</p>
                <button class="btn btn-outline-light" onclick="loadQuizHeatmap()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        `;
    }
    
    startAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
        }
        
        this.autoRefreshTimer = setInterval(() => {
            if (this.currentQuizId && !document.hidden) {
                this.loadQuizHeatmap();
            }
        }, this.refreshInterval);
    }
    
    pauseAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }
    
    resumeAutoRefresh() {
        this.startAutoRefresh();
    }
    
    refreshDashboard() {
        if (this.currentQuizId) {
            this.loadQuizHeatmap();
        }
    }
}

// Global functions for HTML event handlers
let heatmapDashboard;

function initializeHeatmapDashboard() {
    heatmapDashboard = new HeatmapDashboard();
}

function loadQuizHeatmap() {
    heatmapDashboard.loadQuizHeatmap();
}

function setHeatmapView(view) {
    heatmapDashboard.setHeatmapView(view);
}

function refreshDashboard() {
    heatmapDashboard.refreshDashboard();
}

async function acknowledgeInsight(insightId) {
    try {
        const response = await fetch(`/api/heatmap/insights/${insightId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Refresh insights
            loadQuizHeatmap();
        } else {
            alert('Failed to acknowledge insight');
        }
    } catch (error) {
        console.error('Error acknowledging insight:', error);
        alert('Failed to acknowledge insight');
    }
}

function showQuestionDetails(questionId) {
    // Show question detail modal
    const modal = new bootstrap.Modal(document.getElementById('questionDetailModal'));
    
    document.getElementById('questionDetailContent').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading question details...</p>
        </div>
    `;
    
    modal.show();
    
    // TODO: Load detailed question analysis
    setTimeout(() => {
        document.getElementById('questionDetailContent').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Detailed question analysis coming soon!
            </div>
        `;
    }, 1000);
}

function showAnalysisSettings() {
    const modal = new bootstrap.Modal(document.getElementById('analysisSettingsModal'));
    modal.show();
}

function saveAnalysisSettings() {
    const refreshInterval = document.getElementById('refreshInterval').value;
    const enableRealTime = document.getElementById('enableRealTime').checked;
    
    heatmapDashboard.refreshInterval = parseInt(refreshInterval);
    
    if (enableRealTime) {
        heatmapDashboard.startAutoRefresh();
    } else {
        heatmapDashboard.pauseAutoRefresh();
    }
    
    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('analysisSettingsModal')).hide();
}

function exportHeatmapData() {
    if (!heatmapDashboard.currentQuizId) {
        alert('Please select a quiz first');
        return;
    }
    
    // TODO: Implement data export
    alert('Export functionality coming soon!');
}