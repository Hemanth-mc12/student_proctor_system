// static/js/performance_chart.js

export function initPerformanceChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error("Chart canvas not found");
        return;
    }

    if (!data || !data.subjects) {
        console.error("Invalid data:", data);
        return;
    }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.subjects,
            datasets: [
                {
                    label: "Marks (%)",
                    data: data.marks,
                    backgroundColor: "rgba(54,162,235,0.7)",
                    borderColor: "rgba(54,162,235,1)",
                    borderWidth: 1,
                    yAxisID: "y",
                },
                {
                    label: "Attendance (%)",
                    data: data.attendance,
                    type: "line",
                    borderColor: "rgba(255,99,132,1)",
                    borderWidth: 3,
                    tension: 0.3,
                    yAxisID: "y1",
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: "Marks (%)" }
                },
                y1: {
                    beginAtZero: true,
                    max: 100,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: "Attendance (%)" }
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    if (window.performanceData) {
        initPerformanceChart("studentPerformanceChart", window.performanceData);
    }
});
