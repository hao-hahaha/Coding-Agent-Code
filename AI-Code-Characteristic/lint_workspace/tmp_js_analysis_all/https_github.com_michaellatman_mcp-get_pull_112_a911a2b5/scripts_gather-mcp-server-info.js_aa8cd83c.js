#!/usr/bin/env node

/**
 * Script to gather information about MCP servers from GitHub repositories
 * This script helps automate the process of adding MCP servers to mcp-get
 * 
 * Usage: node gather-mcp-server-info.js <github-repo-url>
 * Example: node gather-mcp-server-info.js https://github.com/magarcia/mcp-server-giphy
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import https from 'https';
import { promisify } from 'util';
import { exec as execCallback } from 'child_process';

const exec = promisify(execCallback);

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve(data);
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
}

async function checkNpmPackage(packageName) {
  try {
    const { stdout } = await exec(`npm view ${packageName} --json`);
    return { published: true, data: JSON.parse(stdout) };
  } catch (error) {
    return { published: false, error: error.message };
  }
}

async function checkPyPiPackage(packageName) {
  try {
    const data = await fetchUrl(`https://pypi.org/pypi/${packageName}/json`);
    return { published: true, data: JSON.parse(data) };
  } catch (error) {
    return { published: false, error: error.message };
  }
}

async function extractGitHubInfo(repoUrl) {
  const urlParts = repoUrl.split('/');
  const owner = urlParts[3];
  const repo = urlParts[4];
  
  console.log(`\nGathering information for ${owner}/${repo}...`);
  
  try {
    const { stdout: repoDataStr } = await exec(`gh api repos/${owner}/${repo}`);
    const repoInfo = JSON.parse(repoDataStr);
    
    let packageInfo = null;
    let runtime = null;
    let packageName = null;
    
    try {
      const { stdout: packageJsonData } = await exec(`gh api repos/${owner}/${repo}/contents/package.json --raw`);
      packageInfo = JSON.parse(packageJsonData);
      runtime = 'node';
      packageName = packageInfo.name;
    } catch (pkgError) {
      console.log('No package.json found, checking for pyproject.toml...');
      try {
        const { stdout: pyprojectData } = await exec(`gh api repos/${owner}/${repo}/contents/pyproject.toml --raw`);
        const nameMatch = pyprojectData.match(/name\s*=\s*["']([^"']+)["']/);
        if (nameMatch) {
          packageName = nameMatch[1];
          runtime = 'python';
          packageInfo = { pyprojectToml: pyprojectData };
        }
      } catch (pyError) {
        console.log('No pyproject.toml found either.');
      }
    }
    
    let readmeContent = null;
    try {
      const { stdout: readmeData } = await exec(`gh api repos/${owner}/${repo}/contents/README.md --raw`);
      readmeContent = readmeData;
    } catch (error) {
      console.log('README.md not found.');
    }
    
    let licenseContent = null;
    let license = repoInfo.license ? repoInfo.license.spdx_id : 'Unknown';
    try {
      const { stdout: licenseData } = await exec(`gh api repos/${owner}/${repo}/contents/LICENSE --raw`);
      licenseContent = licenseData;
    } catch (error) {
      console.log('LICENSE file not found, using license from repo info:', license);
    }
    
    let publishStatus = { published: false };
    if (packageName) {
      if (runtime === 'node') {
        publishStatus = await checkNpmPackage(packageName);
      } else if (runtime === 'python') {
        publishStatus = await checkPyPiPackage(packageName);
      }
    }
    
    const envVars = [];
    if (readmeContent) {
      const envVarMatches = readmeContent.match(/[A-Z_]{2,}(_KEY|_TOKEN|_SECRET|_API|_URL|_HOST|_PORT|_USER|_PASS|_DB)/g);
      if (envVarMatches) {
        const uniqueEnvVars = [...new Set(envVarMatches)];
        uniqueEnvVars.forEach(varName => {
          envVars.push({
            name: varName,
            description: `Environment variable for ${varName.toLowerCase().replace(/_/g, ' ')}`,
            required: true
          });
        });
      }
    }
    
    const mcpGetPackage = {
      name: packageName || `${repo}`,
      description: packageInfo?.description || repoInfo.description || `MCP server for ${repo}`,
      runtime: runtime || 'unknown',
      vendor: owner,
      sourceUrl: repoUrl,
      homepage: repoInfo.homepage || repoUrl,
      license: license
    };
    
    const helperEntry = envVars.length > 0 ? {
      requiredEnvVars: envVars.reduce((acc, envVar) => {
        acc[envVar.name] = {
          description: envVar.description,
          required: envVar.required
        };
        return acc;
      }, {})
    } : {};
    
    console.log('\n=== MCP Server Information ===');
    console.log(`Repository: ${repoUrl}`);
    console.log(`Package Name: ${packageName || 'Unknown'}`);
    console.log(`Runtime: ${runtime || 'Unknown'}`);
    console.log(`License: ${license}`);
    console.log(`Published: ${publishStatus.published ? 'Yes' : 'No'}`);
    
    if (publishStatus.published) {
      console.log('\n=== Package JSON for mcp-get ===');
      console.log(JSON.stringify(mcpGetPackage, null, 2));
      
      console.log('\n=== Helper Entry for src/helpers/index.ts ===');
      console.log(`  '${mcpGetPackage.name}': ${JSON.stringify(helperEntry, null, 2)}`);
      
      const outputDir = path.join(process.cwd(), 'gathered-info');
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      fs.writeFileSync(
        path.join(outputDir, `${mcpGetPackage.name}.json`), 
        JSON.stringify(mcpGetPackage, null, 2)
      );
      
      console.log(`\nPackage JSON saved to: ${path.join(outputDir, `${mcpGetPackage.name}.json`)}`);
    } else {
      console.log('\n⚠️ Package is not published. Cannot add to mcp-get.');
    }
    
  } catch (error) {
    console.error('Error gathering information:', error);
  }
}

const repoUrl = process.argv[2];

if (!repoUrl) {
  console.log('Usage: node gather-mcp-server-info.js <github-repo-url>');
  console.log('Example: node gather-mcp-server-info.js https://github.com/magarcia/mcp-server-giphy');
  process.exit(1);
}

(async () => {
  try {
    await extractGitHubInfo(repoUrl);
  } catch (error) {
    console.error(error);
  }
})();
