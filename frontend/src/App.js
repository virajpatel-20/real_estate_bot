import React, { useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [chartData, setChartData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [area, setArea] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setSummary("");
    setChartData([]);
    setTableData([]);
    setArea("");

    try {
      const response = await axios.post("/api/analyze/", {
        query: query,
      });

      const data = response.data;
      setSummary(data.summary);
      setChartData(data.chartData || []);
      setTableData(data.tableData || []);
      setArea(data.area || "");
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-4">
      <h2 className="mb-4 text-center">Mini Real Estate Analysis Chatbot</h2>

      {/* Chat-style input */}
      <div className="card mb-3">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">
                Ask something (e.g., "Analyze Wakad")
              </label>
              <input
                type="text"
                className="form-control"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='e.g. "Analyze Wakad"'
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Send"}
            </button>
          </form>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {/* Chatbot reply */}
      {summary && (
        <div className="card mb-3">
          <div className="card-body">
            <h5 className="card-title">
              Summary {area ? `for ${area}` : ""}
            </h5>
            <p className="card-text">{summary}</p>
          </div>
        </div>
      )}

      {/* Chart */}
      {chartData && chartData.length > 0 && (
        <div className="card mb-3">
          <div className="card-body">
            <h5 className="card-title">Price and Demand Trend</h5>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="price"
                    name="Price"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="demand"
                    name="Demand"
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {tableData && tableData.length > 0 && (
        <div className="card mb-3">
          <div className="card-body">
            <h5 className="card-title">Filtered Data Table</h5>
            <div className="table-responsive">
              <table className="table table-striped table-sm">
                <thead>
                  <tr>
                    {Object.keys(tableData[0]).map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.map((row, idx) => (
                    <tr key={idx}>
                      {Object.keys(row).map((col) => (
                        <td key={col}>{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Small note for assignment */}
      <p className="text-muted text-center mt-3">
        (Backend: Django + pandas, Frontend: React + Bootstrap + Recharts)
      </p>
    </div>
  );
}

export default App;
