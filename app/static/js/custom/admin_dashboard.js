function fetchChartData(url, timeFrame) {
        return fetch(`${url}?timeFrame=${timeFrame}`)
            .then(response => response.json())
            .then(data => data);
    }

    function updateChart(chart, url, timeFrame) {
        fetchChartData(url, timeFrame).then(data => {
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.data;
            chart.update();
        });
    }

    // Text to Image Chart with separate lines for Story and Image Generation
    const textToImageCtx = document.getElementById('textToImageChart').getContext('2d');
    const textToImageChart = new Chart(textToImageCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Story',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'Image Generation',
                    data: [],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            scales: {
                x: { type: 'time', time: { unit: 'day' } },
                y: { beginAtZero: true }
            }
        }
    });

    document.getElementById('textToImageTimeFilter').addEventListener('change', function () {
        updateTextToImageChart(this.value);
    });

    function updateTextToImageChart(timeFrame) {
        fetch(`/admin/text_to_image_requests_chart_data?timeFrame=${timeFrame}`)
            .then(response => response.json())
            .then(data => {
                textToImageChart.data.labels = data.labels;
                textToImageChart.data.datasets[0].data = data.storyData; // Story verisi
                textToImageChart.data.datasets[1].data = data.imageGenerationData; // Image Generation verisi
                textToImageChart.update();
            });
    }

    updateTextToImageChart('daily');  // Sayfa yüklendiğinde günlük veriyle başlatıyoruz

    // Upscale Chart
    const upscaleCtx = document.getElementById('upscaleChart').getContext('2d');
    const upscaleChart = new Chart(upscaleCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Upscale İstekleri',
                data: [],
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            scales: {
                x: { type: 'time', time: { unit: 'day' } },
                y: { beginAtZero: true }
            }
        }
    });

    document.getElementById('upscaleTimeFilter').addEventListener('change', function () {
        updateChart(upscaleChart, '/admin/upscale_requests_chart_data', this.value);
    });

    updateChart(upscaleChart, '/admin/upscale_requests_chart_data', 'daily');

    // Text to Video Chart with separate lines for Story and Video Generation
    let textToVideoCtx = document.getElementById('textToVideoChart').getContext('2d');
    let textToVideoChart = createChart('line');

    document.getElementById('textToVideoTimeFilter').addEventListener('change', function () {
        updateTextToVideoChart(this.value);
    });

    document.getElementById('textToVideoChartType').addEventListener('change', function () {
        updateChartType(this.value);
    });

    function createChart(chartType) {
        return new Chart(textToVideoCtx, {
            type: chartType,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Image To video',
                        data: [],
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        fill: chartType === 'line' ? false : true
                    },
                    {
                        label: 'Text To Video Generation',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        fill: chartType === 'line' ? false : true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: chartType !== 'pie' ? {
                    x: { type: 'time', time: { unit: 'day' } },
                    y: { beginAtZero: true }
                } : undefined
            }
        });
    }

    function updateTextToVideoChart(timeFrame) {
        fetch(`/admin/text_to_video_requests_chart_data?timeFrame=${timeFrame}`)
            .then(response => response.json())
            .then(data => {
                textToVideoChart.data.labels = data.labels;
                textToVideoChart.data.datasets[0].data = data.imageToVideoData; // Image To Video verisi
                textToVideoChart.data.datasets[1].data = data.videoGenerationData; // Text To Video Generation verisi
                textToVideoChart.update();
            });
    }

    function updateChartType(chartType) {
        textToVideoChart.destroy(); // Eski grafiği yok et
        textToVideoChart = createChart(chartType); // Yeni grafik oluştur
        updateTextToVideoChart(document.getElementById('textToVideoTimeFilter').value); // Yeni grafiğe veri yükle
    }

    updateTextToVideoChart('daily');  // Sayfa yüklendiğinde günlük veriyle başlatıyoruz