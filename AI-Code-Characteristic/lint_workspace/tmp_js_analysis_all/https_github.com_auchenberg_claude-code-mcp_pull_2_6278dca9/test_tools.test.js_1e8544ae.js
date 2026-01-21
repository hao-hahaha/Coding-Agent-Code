import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { setupTools } from "../dist/server/tools.js";
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
    this.tools = {};
  }

  tool(name, description, schema, handler) {
    this.tools[name] = { name, description, schema, handler };
  }

  async callTool(name, args) {
    if (!this.tools[name]) {
      throw new Error(`Tool not found: ${name}`);
    }
    return await this.tools[name].handler(args);
  }
}

// Main test function
async function runTests() {
  console.log("Starting tools tests...");
  
  // Setup test environment
  await setup();
  
  // Create mock server and set up tools
  const server = new MockMcpServer();
  setupTools(server);
  
  // Test each tool
  await testBashTool(server);
  await testReadFileTool(server);
  await testListFilesTool(server);
  await testSearchGlobTool(server);
  await testGrepTool(server);
  await testThinkTool(server);
  await testCodeReviewTool(server);
  await testEditFileTool(server);
  
  // Teardown test environment
  await teardown();
  
  console.log("All tools tests completed!");
}

// Individual tool test functions
async function testBashTool(server) {
  console.log("\nTesting bash tool...");
  
  try {
    // Test valid command
    const result = await server.callTool("bash", { command: "echo 'Hello, World!'" });
    console.log("Result:", result);
    
    if (!result.content[0].text.includes("Hello, World!")) {
      throw new Error("Bash tool failed to execute command correctly");
    }
    
    // Test empty command
    const emptyResult = await server.callTool("bash", { command: "" });
    console.log("Empty command result:", emptyResult);
    
    if (!emptyResult.isError) {
      throw new Error("Bash tool should return error for empty command");
    }
    
    // Test banned command
    const bannedResult = await server.callTool("bash", { command: "curl https://example.com" });
    console.log("Banned command result:", bannedResult);
    
    if (!bannedResult.isError) {
      throw new Error("Bash tool should return error for banned command");
    }
    
    console.log("✅ Bash tool tests passed");
  } catch (error) {
    console.error("❌ Bash tool tests failed:", error);
  }
}

async function testReadFileTool(server) {
  console.log("\nTesting readFile tool...");
  
  try {
    // Test valid file
    const testFilePath = path.join(TEST_DIR, "test-file.txt");
    const result = await server.callTool("readFile", { file_path: testFilePath });
    console.log("Result:", result);
    
    if (!result.content[0].text.includes("This is a test file.")) {
      throw new Error("ReadFile tool failed to read file correctly");
    }
    
    // Test with offset and limit
    const offsetResult = await server.callTool("readFile", { 
      file_path: testFilePath,
      offset: 2,
      limit: 1
    });
    console.log("Offset result:", offsetResult);
    
    if (!offsetResult.content[0].text.includes("It has multiple lines.")) {
      throw new Error("ReadFile tool failed to handle offset and limit correctly");
    }
    
    // Test non-existent file
    const nonExistentResult = await server.callTool("readFile", { 
      file_path: path.join(TEST_DIR, "non-existent.txt") 
    });
    console.log("Non-existent file result:", nonExistentResult);
    
    if (!nonExistentResult.isError) {
      throw new Error("ReadFile tool should return error for non-existent file");
    }
    
    console.log("✅ ReadFile tool tests passed");
  } catch (error) {
    console.error("❌ ReadFile tool tests failed:", error);
  }
}

async function testListFilesTool(server) {
  console.log("\nTesting listFiles tool...");
  
  try {
    // Test valid directory
    const result = await server.callTool("listFiles", { path: TEST_DIR });
    console.log("Result:", result);
    
    const files = JSON.parse(result.content[0].text);
    if (!Array.isArray(files) || files.length === 0) {
      throw new Error("ListFiles tool failed to list files correctly");
    }
    
    // Test non-existent directory
    const nonExistentResult = await server.callTool("listFiles", { 
      path: path.join(TEST_DIR, "non-existent-dir") 
    });
    console.log("Non-existent directory result:", nonExistentResult);
    
    if (!nonExistentResult.isError) {
      throw new Error("ListFiles tool should return error for non-existent directory");
    }
    
    console.log("✅ ListFiles tool tests passed");
  } catch (error) {
    console.error("❌ ListFiles tool tests failed:", error);
  }
}

async function testSearchGlobTool(server) {
  console.log("\nTesting searchGlob tool...");
  
  try {
    // Test valid pattern
    const result = await server.callTool("searchGlob", { 
      pattern: "*.txt",
      path: TEST_DIR
    });
    console.log("Result:", result);
    
    if (!result.content[0].text.includes("test-file.txt")) {
      throw new Error("SearchGlob tool failed to find files correctly");
    }
    
    // Test pattern with no matches
    const noMatchResult = await server.callTool("searchGlob", { 
      pattern: "*.pdf",
      path: TEST_DIR
    });
    console.log("No match result:", noMatchResult);
    
    if (!noMatchResult.content[0].text.includes("No files found")) {
      throw new Error("SearchGlob tool should handle no matches gracefully");
    }
    
    console.log("✅ SearchGlob tool tests passed");
  } catch (error) {
    console.error("❌ SearchGlob tool tests failed:", error);
  }
}

async function testGrepTool(server) {
  console.log("\nTesting grep tool...");
  
  try {
    // Test valid pattern
    const result = await server.callTool("grep", { 
      pattern: "test",
      path: TEST_DIR
    });
    console.log("Result:", result);
    
    // Test invalid regex pattern
    const invalidRegexResult = await server.callTool("grep", { 
      pattern: "[",
      path: TEST_DIR
    });
    console.log("Invalid regex result:", invalidRegexResult);
    
    if (!invalidRegexResult.isError) {
      throw new Error("Grep tool should return error for invalid regex pattern");
    }
    
    console.log("✅ Grep tool tests passed");
  } catch (error) {
    console.error("❌ Grep tool tests failed:", error);
  }
}

async function testThinkTool(server) {
  console.log("\nTesting think tool...");
  
  try {
    // Test valid thought
    const result = await server.callTool("think", { 
      thought: "This is a test thought" 
    });
    console.log("Result:", result);
    
    if (!result.content[0].text.includes("This is a test thought")) {
      throw new Error("Think tool failed to process thought correctly");
    }
    
    // Test empty thought
    const emptyResult = await server.callTool("think", { thought: "" });
    console.log("Empty thought result:", emptyResult);
    
    if (!emptyResult.isError) {
      throw new Error("Think tool should return error for empty thought");
    }
    
    console.log("✅ Think tool tests passed");
  } catch (error) {
    console.error("❌ Think tool tests failed:", error);
  }
}

async function testCodeReviewTool(server) {
  console.log("\nTesting codeReview tool...");
  
  try {
    // Test valid code
    const result = await server.callTool("codeReview", { 
      code: "function test() { return 'Hello'; }" 
    });
    console.log("Result:", result);
    
    if (!result.content[0].text.includes("Code review")) {
      throw new Error("CodeReview tool failed to process code correctly");
    }
    
    // Test empty code
    const emptyResult = await server.callTool("codeReview", { code: "" });
    console.log("Empty code result:", emptyResult);
    
    if (!emptyResult.isError) {
      throw new Error("CodeReview tool should return error for empty code");
    }
    
    console.log("✅ CodeReview tool tests passed");
  } catch (error) {
    console.error("❌ CodeReview tool tests failed:", error);
  }
}

async function testEditFileTool(server) {
  console.log("\nTesting editFile tool...");
  
  try {
    // Test creating a new file
    const testFilePath = path.join(TEST_DIR, "new-file.txt");
    const result = await server.callTool("editFile", { 
      file_path: testFilePath,
      content: "This is a new file created by the editFile tool."
    });
    console.log("Result:", result);
    
    // Verify file was created
    const fileContent = await fs.readFile(testFilePath, "utf-8");
    if (fileContent !== "This is a new file created by the editFile tool.") {
      throw new Error("EditFile tool failed to create file correctly");
    }
    
    // Test updating an existing file
    const updateResult = await server.callTool("editFile", { 
      file_path: testFilePath,
      content: "This file has been updated."
    });
    console.log("Update result:", updateResult);
    
    // Verify file was updated
    const updatedContent = await fs.readFile(testFilePath, "utf-8");
    if (updatedContent !== "This file has been updated.") {
      throw new Error("EditFile tool failed to update file correctly");
    }
    
    // Test empty file path
    const emptyPathResult = await server.callTool("editFile", { 
      file_path: "",
      content: "Test content"
    });
    console.log("Empty path result:", emptyPathResult);
    
    if (!emptyPathResult.isError) {
      throw new Error("EditFile tool should return error for empty file path");
    }
    
    console.log("✅ EditFile tool tests passed");
  } catch (error) {
    console.error("❌ EditFile tool tests failed:", error);
  }
}

// Run all tests
runTests().catch(error => {
  console.error("Error running tests:", error);
  process.exit(1);
});
