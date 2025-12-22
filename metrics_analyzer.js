#!/usr/bin/env node
/**
 * Standalone Metrics Analyzer for AI Pattern Recognition
 * JavaScript version - ready for n8n workflow integration
 * 
 * Fetches daily metrics (Total Sales, Net Profit, TACOS, ACOS) and formats for LLM analysis
 * 
 * USAGE:
 *   node metrics_analyzer.js 2025-12-01 2025-12-05
 *   node metrics_analyzer.js 2025-12-01 2025-12-05 B08N5WRWNW
 * 
 * n8n CODE NODE USAGE:
 *   Copy the n8nCodeNode function and return its result
 */

// ============================================================================
// CONFIGURATION - Update these values
// ============================================================================
const BASE_URL = "https://api0.dev.nyle.ai/math/v1";
const BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2MTgwNDQ4LCJpYXQiOjE3NjYxNzY4NDgsImp0aSI6ImI4ZWRhYTAzMjQ2YzRiMDA5NWIzZGZmNzQzMjEzNjBhIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwic2NvcGVzIjoiIiwiYXVkIjpbImFwaSJdLCJpc3MiOiJueWxlLmFpIn0.ejrZH91O6w9KxLCSAZEzB13N7cRkx-NWeHNW7QtaTt8";

const TIMESPAN = "day";

// API Endpoints
const ENDPOINTS = {
  total_sales: "/math/total/sales",
  tacos: "/math/total/tacos",
  acos: "/math/ads/acos",
  net_profit: "/math/cfo/net-profit"
};

// ============================================================================
// FUNCTIONS
// ============================================================================

async function fetchMetric(metricName, dateStart, dateEnd, asin = null) {
  const endpoint = ENDPOINTS[metricName];
  if (!endpoint) {
    return { error: `Unknown metric: ${metricName}` };
  }

  const params = new URLSearchParams({
    timespan: TIMESPAN,
    date_start: dateStart,
    date_end: dateEnd
  });

  if (asin) {
    params.append("asin", asin);
  }

  const url = `${BASE_URL}${endpoint}?${params.toString()}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        accept: "application/json",
        Authorization: `Bearer ${BEARER_TOKEN}`
      }
    });

    if (response.ok) {
      return await response.json();
    } else {
      const text = await response.text();
      return { error: `API Error ${response.status}: ${text}` };
    }
  } catch (e) {
    return { error: `Request failed: ${e.message}` };
  }
}

async function fetchAllMetrics(dateStart, dateEnd, asin = null) {
  const results = {};

  console.log(`Fetching metrics from ${dateStart} to ${dateEnd}...`);

  for (const metricName of Object.keys(ENDPOINTS)) {
    console.log(`  → Fetching ${metricName}...`);
    const data = await fetchMetric(metricName, dateStart, dateEnd, asin);
    results[metricName] = data;
  }

  console.log("✓ All metrics fetched\n");
  return results;
}

function formatForAI(metricsData) {
  // Extract data arrays
  const totalSalesData = metricsData.total_sales?.data || [];
  const tacosData = metricsData.tacos?.data || [];
  const acosData = metricsData.acos?.data || [];
  const netProfitData = metricsData.net_profit?.data || [];

  if (totalSalesData.length === 0) {
    return "ERROR: No data available. Check API connection and token.";
  }

  // Get period info
  const periodStart = metricsData.total_sales?.period_start || "N/A";
  const periodEnd = metricsData.total_sales?.period_end || "N/A";
  const numDays = totalSalesData.length;

  // Build formatted output
  const output = [];
  output.push("=".repeat(80));
  output.push("DAILY METRICS DATA FOR AI ANALYSIS");
  output.push("=".repeat(80));
  output.push(`Period: ${periodStart} to ${periodEnd}`);
  output.push(`Total Days: ${numDays}`);
  output.push("");

  // Daily breakdown
  output.push("-".repeat(80));
  output.push("DAILY BREAKDOWN");
  output.push("-".repeat(80));
  output.push("");

  const dailyRecords = [];

  for (let i = 0; i < numDays; i++) {
    // Extract values for this day
    const date = totalSalesData[i]?.period_start || "N/A";
    const totalSales = totalSalesData[i]?.value || 0;
    const netProfit = i < netProfitData.length ? netProfitData[i]?.value || 0 : 0;
    const tacos = i < tacosData.length ? tacosData[i]?.value || 0 : 0;
    const acos = i < acosData.length ? acosData[i]?.value || 0 : 0;
    const isForecast = totalSalesData[i]?.is_forecast || false;

    // Format daily output
    output.push(`Day ${i + 1}: ${date}`);
    output.push(`  • Total Sales:    $${totalSales.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
    output.push(`  • Net Profit:     $${netProfit.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
    output.push(`  • TACOS:          ${(tacos * 100).toFixed(2)}%`);
    output.push(`  • ACOS:           ${(acos * 100).toFixed(2)}%`);

    if (isForecast) {
      output.push(`  • [FORECASTED]`);
    }

    output.push("");

    // Store for JSON
    dailyRecords.push({
      day: i + 1,
      date: date,
      total_sales: Math.round(totalSales * 100) / 100,
      net_profit: Math.round(netProfit * 100) / 100,
      tacos: Math.round(tacos * 10000) / 10000,
      acos: Math.round(acos * 10000) / 10000,
      is_forecast: isForecast
    });
  }

  // Statistical summary
  output.push("-".repeat(80));
  output.push("STATISTICAL SUMMARY");
  output.push("-".repeat(80));
  output.push("");

  const totalSalesValues = totalSalesData.map(d => d?.value || 0);
  const netProfitValues = netProfitData.map(d => d?.value || 0);
  const tacosValues = tacosData.map(d => d?.value || 0);
  const acosValues = acosData.map(d => d?.value || 0);

  const sum = arr => arr.reduce((a, b) => a + b, 0);
  const avg = arr => arr.length > 0 ? sum(arr) / arr.length : 0;

  output.push("Total Sales:");
  output.push(`  • Sum:        $${sum(totalSalesValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Average:    $${avg(totalSalesValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Highest:    $${Math.max(...totalSalesValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Lowest:     $${Math.min(...totalSalesValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push("");

  output.push("Net Profit:");
  output.push(`  • Sum:        $${sum(netProfitValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Average:    $${avg(netProfitValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Highest:    $${Math.max(...netProfitValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push(`  • Lowest:     $${Math.min(...netProfitValues).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
  output.push("");

  output.push("TACOS (Total Advertising Cost of Sales):");
  output.push(`  • Average:    ${(avg(tacosValues) * 100).toFixed(2)}%`);
  output.push(`  • Highest:    ${(Math.max(...tacosValues) * 100).toFixed(2)}%`);
  output.push(`  • Lowest:     ${(Math.min(...tacosValues) * 100).toFixed(2)}%`);
  output.push("");

  output.push("ACOS (Advertising Cost of Sales):");
  output.push(`  • Average:    ${(avg(acosValues) * 100).toFixed(2)}%`);
  output.push(`  • Highest:    ${(Math.max(...acosValues) * 100).toFixed(2)}%`);
  output.push(`  • Lowest:     ${(Math.min(...acosValues) * 100).toFixed(2)}%`);
  output.push("");

  // JSON format for programmatic use
  output.push("-".repeat(80));
  output.push("STRUCTURED DATA (JSON)");
  output.push("-".repeat(80));
  output.push("");
  output.push(JSON.stringify(dailyRecords, null, 2));
  output.push("");
  output.push("=".repeat(80));

  return {
    formatted: output.join("\n"),
    data: dailyRecords,
    summary: {
      period_start: periodStart,
      period_end: periodEnd,
      total_days: numDays,
      total_sales_sum: sum(totalSalesValues),
      net_profit_sum: sum(netProfitValues),
      avg_tacos: avg(tacosValues),
      avg_acos: avg(acosValues)
    }
  };
}

async function analyzeMetrics(dateStart, dateEnd, asin = null) {
  console.log("\n" + "=".repeat(60));
  console.log("NYLE METRICS ANALYZER");
  console.log("=".repeat(60));

  // Fetch all metrics
  const metricsData = await fetchAllMetrics(dateStart, dateEnd, asin);

  // Format for AI
  const result = formatForAI(metricsData);

  return result;
}

// ============================================================================
// n8n CODE NODE VERSION
// ============================================================================
/**
 * Copy this function into an n8n Code node
 * Input: items with date_start, date_end, and optional asin fields
 * 
 * IMPORTANT: n8n expects return format: [{ json: { ... } }]
 */
async function n8nCodeNode(items) {
  // Get input from previous node
  const input = items[0].json;
  const dateStart = input.date_start;
  const dateEnd = input.date_end;
  const asin = input.asin || null;

  // Configuration
  const BASE_URL = "https://api0.dev.nyle.ai/math/v1";
  const BEARER_TOKEN = "YOUR_TOKEN_HERE"; // Replace with actual token
  const TIMESPAN = "day";
  
  const ENDPOINTS = {
    total_sales: "/math/total/sales",
    tacos: "/math/total/tacos",
    acos: "/math/ads/acos",
    net_profit: "/math/cfo/net-profit"
  };

  // Fetch all metrics
  const results = {};
  for (const [metricName, endpoint] of Object.entries(ENDPOINTS)) {
    const params = new URLSearchParams({
      timespan: TIMESPAN,
      date_start: dateStart,
      date_end: dateEnd
    });
    if (asin) params.append("asin", asin);

    const url = `${BASE_URL}${endpoint}?${params.toString()}`;
    
    const response = await fetch(url, {
      method: "GET",
      headers: {
        accept: "application/json",
        Authorization: `Bearer ${BEARER_TOKEN}`
      }
    });
    
    results[metricName] = await response.json();
  }

  // Process data
  const totalSalesData = results.total_sales?.data || [];
  const dailyRecords = totalSalesData.map((item, i) => ({
    day: i + 1,
    date: item.period_start,
    total_sales: item.value,
    net_profit: results.net_profit?.data?.[i]?.value || 0,
    tacos: results.tacos?.data?.[i]?.value || 0,
    acos: results.acos?.data?.[i]?.value || 0,
    is_forecast: item.is_forecast || false
  }));

  // n8n REQUIRES this exact format: array of objects with json property
  return [{
    json: {
      success: true,
      period_start: dateStart,
      period_end: dateEnd,
      total_days: dailyRecords.length,
      daily_metrics: dailyRecords,
      formatted_output: dailyRecords.map(d => 
        `Day ${d.day} (${d.date}): Sales $${d.total_sales.toFixed(2)}, Profit $${d.net_profit.toFixed(2)}, TACOS ${(d.tacos * 100).toFixed(2)}%, ACOS ${(d.acos * 100).toFixed(2)}%`
      ).join("\n")
    }
  }];
}

// ============================================================================
// MAIN EXECUTION (for CLI)
// ============================================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log("\n" + "=".repeat(60));
    console.log("USAGE");
    console.log("=".repeat(60));
    console.log("\nBasic:");
    console.log("  node metrics_analyzer.js <date_start> <date_end>");
    console.log("\nWith ASIN filter:");
    console.log("  node metrics_analyzer.js <date_start> <date_end> <asin>");
    console.log("\nExamples:");
    console.log("  node metrics_analyzer.js 2025-12-01 2025-12-05");
    console.log("  node metrics_analyzer.js 2025-12-01 2025-12-05 B08N5WRWNW");
    console.log("\n" + "=".repeat(60) + "\n");
    process.exit(1);
  }

  const dateStart = args[0];
  const dateEnd = args[1];
  const asin = args[2] || null;

  // Run analysis
  const result = await analyzeMetrics(dateStart, dateEnd, asin);

  // Print formatted result
  console.log(result.formatted);

  // Save to file
  const fs = await import("fs");
  const outputFile = `metrics_${dateStart}_to_${dateEnd}.txt`;
  fs.writeFileSync(outputFile, result.formatted);
  console.log(`\n✓ Output saved to: ${outputFile}\n`);

  // Also output JSON for programmatic use
  const jsonFile = `metrics_${dateStart}_to_${dateEnd}.json`;
  fs.writeFileSync(jsonFile, JSON.stringify(result, null, 2));
  console.log(`✓ JSON saved to: ${jsonFile}\n`);
}

main().catch(console.error);


