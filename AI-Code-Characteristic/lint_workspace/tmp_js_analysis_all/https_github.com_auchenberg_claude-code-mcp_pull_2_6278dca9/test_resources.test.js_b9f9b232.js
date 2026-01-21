import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { setupResources } from "../dist/server/resources.js";
import * as fs from "fs/promises";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create a temporary directory for test files
const TEST_DIR = path.join(__dirname, "temp");

// Setup and teardown functions
async function setup() {
  try {
    await fs.mkdir(TEST_DIR, { recursive: true });
    await fs.writeFile(path.join(TEST_DIR, "test-file.txt"), "This is a test file.\nIt has multiple lines.\nFor testing purposes.");
  } catch (error) {
    console.error("Error in setup:", error);
  }
}

async function teardown() {
  try {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  } catch (error) {
    console.error("Error in teardown:", error);
  }
}

// Mock McpServer class for testing
class MockMcpServer {
  constructor() {
    this.resources = {};
  }

  resource(name, template, handler) {
    this.resources[name] = { name, template, handler };
  }

  async callResource(name, uri, variables = {}) {
    if (!this.resources[name]) {
      throw new Error(`Resource not found: ${name}`);
    }
    return await this.resources[name].handler(new URL(uri), variables);
  }
}

// Main test function
async function runTests() {
  console.log("Starting resources tests...");
  
  // Setup test environment
  await setup();
  
  // Create mock server and set up resources
  const server = new MockMcpServer();
  setupResources(server);
  
  // Test each resource
  await testFileResource(server);
  await testDirectoryResource(server);
  await testEnvironmentResource(server);
  
  // Teardown test environment
  await teardown();
  
  console.log("All resources tests completed!");
}

// Individual resource test functions
async function testFileResource(server) {
  console.log("\nTesting file resource...");
  
  try {
    // Test valid file
    const testFilePath = path.join(TEST_DIR, "test-file.txt");
    const result = await server.callResource(
      "file", 
      `file://${testFilePath}`,
      { path: testFilePath }
    );
    console.log("Result:", result);
    
    if (!result.contents[0].text.includes("This is a test file.")) {
      throw new Error("File resource failed to read file correctly");
    }
    
    // Test non-existent file
    const nonExistentResult = await server.callResource(
      "file", 
      `file://${path.join(TEST_DIR, "non-existent.txt")}`,
      { path: path.join(TEST_DIR, "non-existent.txt") }
    );
    console.log("Non-existent file result:", nonExistentResult);
    
    if (!nonExistentResult.isError) {
      throw new Error("File resource should return error for non-existent file");
    }
    
    // Test missing path
    const missingPathResult = await server.callResource(
      "file", 
      `file://missing`,
      { }
    );
    console.log("Missing path result:", missingPathResult);
    
    if (!missingPathResult.isError) {
      throw new Error("File resource should return error for missing path");
    }
    
    console.log("✅ File resource tests passed");
  } catch (error) {
    console.error("❌ File resource tests failed:", error);
  }
}

async function testDirectoryResource(server) {
  console.log("\nTesting directory resource...");
  
  try {
    // Test valid directory
    const result = await server.callResource(
      "directory", 
      `dir://${TEST_DIR}`,
      { path: TEST_DIR }
    );
    console.log("Result:", result);
    
    const files = JSON.parse(result.contents[0].text);
    if (!Array.isArray(files) || files.length === 0) {
      throw new Error("Directory resource failed to list files correctly");
    }
    
    // Test non-existent directory
    const nonExistentResult = await server.callResource(
      "directory", 
      `dir://${path.join(TEST_DIR, "non-existent-dir")}`,
      { path: path.join(TEST_DIR, "non-existent-dir") }
    );
    console.log("Non-existent directory result:", nonExistentResult);
    
    if (!nonExistentResult.isError) {
      throw new Error("Directory resource should return error for non-existent directory");
    }
    
    // Test missing path
    const missingPathResult = await server.callResource(
      "directory", 
      `dir://missing`,
      { }
    );
    console.log("Missing path result:", missingPathResult);
    
    if (!missingPathResult.isError) {
      throw new Error("Directory resource should return error for missing path");
    }
    
    console.log("✅ Directory resource tests passed");
  } catch (error) {
    console.error("❌ Directory resource tests failed:", error);
  }
}

async function testEnvironmentResource(server) {
  console.log("\nTesting environment resource...");
  
  try {
    // Test environment info
    const result = await server.callResource(
      "environment", 
      `env://info`,
      { }
    );
    console.log("Result:", result);
    
    const envInfo = JSON.parse(result.contents[0].text);
    if (!envInfo.node || !envInfo.npm || !envInfo.os || !envInfo.env) {
      throw new Error("Environment resource failed to provide complete environment information");
    }
    
    // Check for sensitive information redaction
    const sensitiveKeys = ['TOKEN', 'KEY', 'SECRET', 'PASSWORD', 'CREDENTIAL', 'AUTH'];
    const envVars = envInfo.env;
    
    // Add a fake sensitive environment variable for testing
    process.env.TEST_API_KEY = "sensitive-value";
    
    // Call the resource again to get updated environment info
    const updatedResult = await server.callResource(
      "environment", 
      `env://info`,
      { }
    );
    
    const updatedEnvInfo = JSON.parse(updatedResult.contents[0].text);
    const updatedEnvVars = updatedEnvInfo.env;
    
    // Check if the sensitive value is redacted
    if (updatedEnvVars.TEST_API_KEY !== "[REDACTED]") {
      throw new Error("Environment resource failed to redact sensitive information");
    }
    
    // Clean up the test environment variable
    delete process.env.TEST_API_KEY;
    
    console.log("✅ Environment resource tests passed");
  } catch (error) {
    console.error("❌ Environment resource tests failed:", error);
  }
}

// Run all tests
runTests().catch(error => {
  console.error("Error running tests:", error);
  process.exit(1);
});
