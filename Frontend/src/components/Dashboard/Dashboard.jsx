import React, { useEffect, useState, useMemo } from "react";
import { Pie, Bar, Line, Doughnut } from "react-chartjs-2";
import "../Dashboard/Dashboard.css";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  BarElement,
  ArcElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  BarElement,
  ArcElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const Dashboard = ({ fileId }) => {
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState({});
  const [totalRows, setTotalRows] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(1000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [columnTypes, setColumnTypes] = useState({});
  const [visualizationSuggestions, setVisualizationSuggestions] = useState(null);
  const [trends, setTrends] = useState([]);
  const [keyTakeaways, setKeyTakeaways] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `http://localhost:5000/data/${fileId}?page=${page}&per_page=${perPage}`
        );
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Data Fetch Error: ${response.status} - ${errorData.error || "Unknown error"}`);
        }
        const result = await response.json();
        setData(Array.isArray(result.data) ? result.data : []);
        setSummary(result.summary || {});
        setTotalRows(result.total_rows || 0);
        setVisualizationSuggestions(result.visualization_suggestions || null);
        setTrends(result.summary.trends || []);
        setKeyTakeaways(result.summary.key_takeaways || []);
        const types = {};
        if (result.summary?.columns) {
          Object.entries(result.summary.columns).forEach(([col, info]) => {
            types[col] = /float|int/.test(info.type) && !col.toLowerCase().includes("id") ? "numerical" : "categorical";
          });
        }
        setColumnTypes(types);
      } catch (err) {
        setError(err.message);
        setData([]);
        setSummary({});
        setTotalRows(0);
        setVisualizationSuggestions(null);
        setTrends([]);
        setKeyTakeaways([]);
      } finally {
        setLoading(false);
      }
    };
    if (fileId) fetchData();
  }, [fileId, page, perPage]);

  const totalPages = useMemo(() => Math.ceil(totalRows / perPage), [totalRows, perPage]);
  const numericalCols = useMemo(() => Object.keys(columnTypes).filter(col => columnTypes[col] === "numerical"), [columnTypes]);
  const categoricalCols = useMemo(() => Object.keys(columnTypes).filter(col => columnTypes[col] === "categorical"), [columnTypes]);
  const dateCols = useMemo(() => Object.keys(columnTypes).filter(col => col.toLowerCase().includes("date")), [columnTypes]);

  const getUniqueValues = (col) => [...new Set(data.map(row => row[col]))].filter(v => v != null);
  const aggregateSum = (catCol, numCol) =>
    getUniqueValues(catCol).map(cat =>
      data.filter(row => row[catCol] === cat).reduce((sum, row) => sum + (parseFloat(row[numCol]) || 0), 0)
    );
  const aggregateAvg = (catCol, numCol) =>
    getUniqueValues(catCol).map(cat => {
      const values = data.filter(row => row[catCol] === cat).map(row => parseFloat(row[numCol]) || 0);
      return values.length ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
    });
  const aggregateCount = (col) => getUniqueValues(col).map(val => data.filter(row => row[col] === val).length);
  const timeSeriesData = (timeCol, valueCol) => {
    const sortedData = [...data].sort((a, b) => new Date(a[timeCol]) - new Date(b[timeCol]));
    return sortedData.map(row => ({ x: new Date(row[timeCol]), y: parseFloat(row[valueCol]) || 0 }));
  };

  const visualizations = useMemo(() => {
    if (loading || error || !data.length || !summary.columns || !visualizationSuggestions) return [];

    const viz = [];
    const suggestions = visualizationSuggestions.split("\n").filter(line => line.trim());

    suggestions.forEach((suggestion, idx) => {
      const matchLine = suggestion.match(/use a (line|bar|pie|doughnut) chart for '([^']+)' vs '([^']+)'/i);
      const matchSingle = suggestion.match(/use a (bar|pie|doughnut) chart for '([^']+)'/i);

      if (matchLine) {
        const [, chartType, col1, col2] = matchLine;
        if (!data[0]?.[col1] || !data[0]?.[col2]) return;

        if (chartType.toLowerCase() === "line" && numericalCols.includes(col2) && dateCols.includes(col1)) {
          viz.push(
            <div key={`viz-${idx}`} className="chart-container">
              <h3>{col2} Trend Over {col1}</h3>
              <Line
                data={{
                  datasets: [{
                    label: col2,
                    data: timeSeriesData(col1, col2),
                    borderColor: "#ff6384",
                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                    fill: true,
                    tension: 0.4,
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" }, title: { display: true, text: `${col2} Trend Over ${col1}`, font: { size: 18 } } },
                  scales: { x: { type: "time", title: { display: true, text: col1 } }, y: { title: { display: true, text: col2 } } },
                  animation: { duration: 1500, easing: "easeInOutQuart" },
                }}
              />
            </div>
          );
        } else if (chartType.toLowerCase() === "bar" && categoricalCols.includes(col1) && numericalCols.includes(col2)) {
          viz.push(
            <div key={`viz-${idx}`} className="chart-container">
              <h3>Total {col2} by {col1}</h3>
              <Bar
                data={{
                  labels: getUniqueValues(col1).slice(0, 10),
                  datasets: [{
                    label: `Total ${col2}`,
                    data: aggregateSum(col1, col2).slice(0, 10),
                    backgroundColor: "rgba(54, 162, 235, 0.8)",
                    borderColor: "#36A2EB",
                    borderWidth: 1,
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" }, title: { display: true, text: `Total ${col2} by ${col1}`, font: { size: 18 } } },
                  scales: { y: { beginAtZero: true, title: { display: true, text: `Total ${col2}` } }, x: { title: { display: true, text: col1 } } },
                  animation: { duration: 1000, easing: "easeOutBounce" },
                }}
              />
            </div>
          );
        } else if (chartType.toLowerCase() === "pie" && categoricalCols.includes(col1) && numericalCols.includes(col2)) {
          viz.push(
            <div key={`viz-${idx}`} className="chart-container">
              <h3>{col2} Distribution by {col1}</h3>
              <Pie
                data={{
                  labels: getUniqueValues(col1).slice(0, 8),
                  datasets: [{
                    label: col2,
                    data: aggregateSum(col1, col2).slice(0, 8),
                    backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#E7E9ED", "#C9CBCF"],
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" }, title: { display: true, text: `${col2} Distribution by ${col1}`, font: { size: 18 } } },
                  animation: { duration: 1200, easing: "easeInOutQuad" },
                }}
              />
            </div>
          );
        }
      } else if (matchSingle) {
        const [, chartType, col] = matchSingle;
        if (!data[0]?.[col]) return;

        if ((chartType.toLowerCase() === "doughnut" || chartType.toLowerCase() === "pie") && categoricalCols.includes(col)) {
          viz.push(
            <div key={`viz-${idx}`} className="chart-container">
              <h3>{col} Distribution</h3>
              <Doughnut
                data={{
                  labels: getUniqueValues(col).slice(0, 8),
                  datasets: [{
                    label: "Count",
                    data: aggregateCount(col).slice(0, 8),
                    backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#E7E9ED", "#C9CBCF"],
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" }, title: { display: true, text: `${col} Distribution`, font: { size: 18 } } },
                  animation: { duration: 1200, easing: "easeInOutQuad" },
                }}
              />
            </div>
          );
        } else if (chartType.toLowerCase() === "bar" && numericalCols.includes(col)) {
          viz.push(
            <div key={`viz-${idx}`} className="chart-container">
              <h3>{col} Values (Sample)</h3>
              <Bar
                data={{
                  labels: data.slice(0, 10).map((_, i) => `Entry ${i + 1}`),
                  datasets: [{
                    label: col,
                    data: data.slice(0, 10).map(row => parseFloat(row[col]) || 0),
                    backgroundColor: "rgba(54, 162, 235, 0.8)",
                    borderColor: "#36A2EB",
                    borderWidth: 1,
                  }],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { position: "top" }, title: { display: true, text: `${col} Values (Sample)`, font: { size: 18 } } },
                  scales: { y: { beginAtZero: true, title: { display: true, text: col } }, x: { title: { display: true, text: "Entries" } } },
                  animation: { duration: 1000, easing: "easeOutBounce" },
                }}
              />
            </div>
          );
        }
      }
    });

    if (!viz.length) {
      viz.push(
        <div key="no-viz" className="chart-container">
          <h3>No Visualizations Available</h3>
          <p>{visualizationSuggestions || "No valid visualization suggestions received."}</p>
        </div>
      );
    }

    return viz;
  }, [loading, error, data, summary, visualizationSuggestions, numericalCols, categoricalCols, dateCols]);

  return (
    <div className="dashboard">
      <h2>AI-Driven Business Insights</h2>
      {loading && <div className="status loading">Analyzing your data...</div>}
      {error && <div className="status error">{error}</div>}
      {!loading && !error && (!data.length || !summary.columns) && (
        <div className="status">Upload data to see insights!</div>
      )}
      {!loading && !error && data.length > 0 && summary.columns && (
        <>
          <div className="summary">
            <h3>Dataset Summary</h3>
            <p><strong>Rows:</strong> {summary.num_rows}</p>
            <p><strong>Columns:</strong> {summary.num_columns}</p>
            <table>
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Unique Values</th>
                  <th>Missing</th>
                  <th>Key Stats</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.columns).map(([col, info]) => (
                  <tr key={col}>
                    <td>{col}</td>
                    <td>{info.type}</td>
                    <td>{info.unique_values}</td>
                    <td>{info.missing_values}</td>
                    <td>
                      {info.mean ? `Mean: ${info.mean.toFixed(2)}, Max: ${info.max}, Min: ${info.min}` : `Top: ${info.top_value}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {keyTakeaways.length > 0 && (
            <div className="key-takeaways">
              <h3>Key Takeaways</h3>
              <ul>
                {keyTakeaways.map((takeaway, idx) => (
                  <li key={idx}>{takeaway}</li>
                ))}
              </ul>
            </div>
          )}
          {trends.length > 0 && (
            <div className="trends">
              <h3>Trends & Predictions</h3>
              <ul>
                {trends.map((trend, idx) => (
                  <li key={idx}>{trend} {trend.includes("increasing") ? "(Expect growth!)" : "(Watch for decline!)"}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="visualizations">{visualizations}</div>
          {totalRows > perPage && (
            <div className="pagination">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Next</button>
              <select value={perPage} onChange={(e) => setPerPage(Number(e.target.value))}>
                <option value={100}>100</option>
                <option value={500}>500</option>
                <option value={1000}>1000</option>
              </select>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;