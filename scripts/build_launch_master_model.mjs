import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "file:///C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const outputPath = "demo-data/Launch_Master_Model.xlsx";
const workbook = Workbook.create();
const sheetNames = ["Reference Data", "Base Inputs", "Sensitivity Inputs", "Calculation Engine", "P&L", "Outputs"];
for (const name of sheetNames) workbook.worksheets.add(name);

const reference = workbook.worksheets.getItem("Reference Data");
reference.getRange("A1:D3").values = [
  ["Reference", "Value", "Unit", "Source"],
  ["Discount Rate", 0.10, "%", "Corporate Launch Discount Rate"],
  ["Forecast Years", 5, "Years", "Launch Sandbox standard horizon"],
];

const base = workbook.worksheets.getItem("Base Inputs");
base.getRange("A1:H9").values = [
  ["Driver", "Unit", "Source", "Y1", "Y2", "Y3", "Y4", "Y5"],
  ["Market Share", "%", "Marketing Workstream", 0.05, 0.12, 0.20, 0.27, 0.31],
  ["Treatment Eligibility", "%", "Medical Workstream", 0.64, 0.64, 0.64, 0.64, 0.64],
  ["Sales Coverage", "%", "Sales Workstream", 0.55, 0.55, 0.55, 0.55, 0.55],
  ["Access Reach", "%", "Market Access Workstream", 0.10, 0.25, 0.45, 0.59, 0.70],
  ["Net Price", "Local currency", "Market Access Workstream", 22263, 22263, 22263, 22263, 22263],
  ["Regulatory Timing", "Date", "Regulatory Workstream", 0, 0, 0, 0, 0],
  ["COGS", "Local currency / unit", "Finance Workstream", 7150, 7150, 7150, 7150, 7150],
  ["Discount Rate", "%", "Finance Reference Data", 0.10, 0.10, 0.10, 0.10, 0.10],
];

const sensitivity = workbook.worksheets.getItem("Sensitivity Inputs");
sensitivity.getRange("A1:I9").values = [
  ["Driver", "Owner", "Unit", "Method", "Model Input", "Affects", "Downstream", "Default Downside", "Default Upside"],
  ["Market Share", "Marketing", "pp", "RAMP_PP", "Market Share PP", "Patients on Product", "Units, Revenue, Gross Profit, Operating Profit, NPV", -5, 5],
  ["Treatment Eligibility", "Medical", "% relative", "ALL_YEARS_RELATIVE", "Treatment Eligibility", "Treated Patients", "Accessible Patients, Units, Revenue, Profit, NPV", -10, 10],
  ["Sales Coverage", "Sales", "% relative", "RAMP_RELATIVE", "Sales Coverage", "Market Share", "Patients on Product, Units, Revenue, Profit, NPV", -10, 10],
  ["Access Reach", "Market Access", "pp", "RAMP_PP", "Access Rate PP", "Accessible Patients", "Patients on Product, Units, Revenue, Profit, NPV", -10, 10],
  ["Net Price", "Market Access", "% relative", "ALL_YEARS_RELATIVE", "Net Price", "Realized Net Price", "Revenue, Gross Profit, Operating Profit, NPV", -10, 5],
  ["Regulatory Timing", "Regulatory", "days", "DAYS_SHIFT", "Timing Shift Days", "Commercial availability", "Patients, Units, Revenue, Profit, NPV", 180, -30],
  ["COGS", "Finance", "% relative", "ALL_YEARS_RELATIVE", "COGS", "COGS per Unit", "Gross Profit, Gross Margin, Operating Profit, NPV", 10, -5],
  ["Discount Rate", "Finance", "pp", "NPV_PP", "Discount Rate PP", "Discount Rate", "NPV only", 2, -2],
];

const engine = workbook.worksheets.getItem("Calculation Engine");
engine.getRange("A1:I4").values = [
  ["Scenario", "Driver", "Year", "Base Input", "Sensitivity Adjustment", "Method", "Scenario Input", "Model Output", "Formula Purpose"],
  ["Downside", "Market Share", "Y5", 0.31, -5, "RAMP_PP", null, "Patients on Product", "Base plus percentage-point deviation, capped 0%-100%"],
  ["Downside", "COGS", "Y5", 7150, 10, "ALL_YEARS_RELATIVE", null, "Gross Profit", "Base multiplied by one plus relative deviation"],
  ["Downside", "Discount Rate", "Y5", 0.10, 2, "NPV_PP", null, "5Y NPV", "Base discount rate plus percentage-point deviation"],
];
engine.getRange("G2:G4").formulas = [
  ["=MAX(0,MIN(1,D2+E2/100))"],
  ["=D3*(1+E3/100)"],
  ["=MAX(0,D4+E4/100)"],
];

const pnl = workbook.worksheets.getItem("P&L");
pnl.getRange("A1:I6").values = [
  ["Scenario", "Year", "Net Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Profit", "Launch Cash Flow Proxy", "Cumulative Launch Cash Flow"],
  ["Base", "Y1", 0, 0, null, 0, null, null, null],
  ["Base", "Y2", 0, 0, null, 0, null, null, null],
  ["Base", "Y3", 0, 0, null, 0, null, null, null],
  ["Base", "Y4", 0, 0, null, 0, null, null, null],
  ["Base", "Y5", 0, 0, null, 0, null, null, null],
];
pnl.getRange("E2:E6").formulas = [["=C2-D2"], ["=C3-D3"], ["=C4-D4"], ["=C5-D5"], ["=C6-D6"]];
pnl.getRange("G2:G6").formulas = [["=E2-F2"], ["=E3-F3"], ["=E4-F4"], ["=E5-F5"], ["=E6-F6"]];
pnl.getRange("H2:H6").formulas = [["=G2"], ["=G3"], ["=G4"], ["=G5"], ["=G6"]];
pnl.getRange("I2:I6").formulas = [["=H2"], ["=I2+H3"], ["=I3+H4"], ["=I4+H5"], ["=I5+H6"]];

const outputs = workbook.worksheets.getItem("Outputs");
outputs.getRange("A1:C7").values = [
  ["Output", "Value", "Definition"],
  ["Y5 Net Revenue", null, "Integrated model Net Revenue in Y5"],
  ["Y5 Operating Profit", null, "Integrated model Operating Profit in Y5"],
  ["5Y Cumulative Revenue", null, "Sum of Y1-Y5 Net Revenue"],
  ["5Y Cumulative Operating Profit", null, "Sum of Y1-Y5 Operating Profit"],
  ["5Y NPV", null, "Discounted Y1-Y5 launch cash-flow proxy"],
  ["Payback Period", null, "Point when cumulative undiscounted launch cash flow becomes positive"],
];
outputs.getRange("B2:B7").formulas = [
  ["='P&L'!C6"],
  ["='P&L'!G6"],
  ["=SUM('P&L'!C2:C6)"],
  ["=SUM('P&L'!G2:G6)"],
  ["=NPV('Reference Data'!B2,'P&L'!H2:H6)"],
  ["=IF('P&L'!I2>=0,\"<1 year\",IF('P&L'!I3>=0,1+(-'P&L'!I2/'P&L'!H3),IF('P&L'!I4>=0,2+(-'P&L'!I3/'P&L'!H4),IF('P&L'!I5>=0,3+(-'P&L'!I4/'P&L'!H5),IF('P&L'!I6>=0,4+(-'P&L'!I5/'P&L'!H6),\">5 years\")))))"],
];

for (const name of sheetNames) {
  const sheet = workbook.worksheets.getItem(name);
  sheet.showGridLines = false;
  const used = sheet.getUsedRange();
  used.format.font = { name: "Aptos", size: 10, color: "#23354D" };
  used.format.verticalAlignment = "center";
  used.format.wrapText = true;
  const header = used.getRow(0);
  header.format.fill = "#EAF0F6";
  header.format.font = { name: "Aptos", size: 10, bold: true, color: "#17324D" };
  header.format.borders = { preset: "bottom", style: "thin", color: "#AEBECD" };
  used.format.autofitColumns();
  used.format.autofitRows();
  sheet.freezePanes.freezeRows(1);
}

reference.getRange("B2").format.numberFormat = "0.0%";
base.getRange("D2:H5").format.numberFormat = "0.0%";
base.getRange("D9:H9").format.numberFormat = "0.0%";
engine.getRange("D2:G2").format.numberFormat = "0.0%";
engine.getRange("D4:G4").format.numberFormat = "0.0%";

await fs.mkdir("demo-data", { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const inspection = await workbook.inspect({ kind: "sheet,formula", maxChars: 5000, options: { maxResults: 80 } });
console.log(inspection.ndjson);
