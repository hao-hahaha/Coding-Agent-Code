import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REQUIRED_FIELDS = ['name', 'description', 'vendor', 'sourceUrl', 'homepage', 'license', 'runtime'];
const VALID_RUNTIMES = ['node', 'python', 'go'];

/**
 * Normalizes a package name for npm/PyPI validation
 * Converts spaces to hyphens, makes lowercase, and handles special characters
 */
export function normalizePackageName(name, runtime) {
  if (!name) return '';
  
  // Convert to lowercase and replace spaces with hyphens
  let normalized = name.toLowerCase().replace(/\s+/g, '-');
  
  if (runtime === 'node') {
    // For npm packages, remove special characters not allowed in npm package names
    normalized = normalized.replace(/[^a-z0-9-_.]/g, '');
  } else if (runtime === 'python') {
    // For Python packages, replace underscores with hyphens for PyPI
    normalized = normalized.replace(/_/g, '-');
  }
  
  return normalized;
}

/**
 * Converts a package name to a safe filename
 * This matches the logic in package-registry.ts
 */
export function getPackageFilename(packageName) {
  return packageName.replace(/^@/, '').replace(/\//g, '--');
}

async function validatePackages() {
  const packageListPath = path.join(__dirname, '../../packages/package-list.json');
  const packagesDir = path.join(__dirname, '../../packages');
  let newPackages = [];

  // Check if we're using the new registry structure (individual package files)
  if (fs.existsSync(packagesDir) && fs.statSync(packagesDir).isDirectory()) {
    console.log('Using new package structure...');
    
    // Get modified or added package files from git diff
    try {
      const diffOutput = execSync(`git diff --name-status origin/main -- packages/`).toString();
      const changedFiles = diffOutput
        .split('\n')
        .filter(line => line.trim())
        .filter(line => line.startsWith('A') || line.startsWith('M'))
        .map(line => line.split('\t')[1])
        .filter(file => file.endsWith('.json') && file !== 'packages/package-list.json');
      
      // Parse each changed package file
      for (const file of changedFiles) {
        try {
          const content = fs.readFileSync(file, 'utf-8');
          const pkg = JSON.parse(content);
          
          // Validate filename matches package name
          const filename = path.basename(file, '.json');
          const expectedFilename = getPackageFilename(pkg.name);
          if (filename !== expectedFilename) {
            throw new Error(`Filename '${filename}' does not match expected filename '${expectedFilename}' for package '${pkg.name}'. Please rename the file.`);
          }
          
          newPackages.push(pkg);
        } catch (error) {
          console.warn(`Warning: Failed to parse package file ${file}: ${error.message}`);
        }
      }
    } catch (error) {
      console.warn(`Warning: Failed to get git diff for registry: ${error.message}`);
    }
  } 
  
  // If no packages found in registry or registry doesn't exist, fall back to package-list.json
  if (newPackages.length === 0 && fs.existsSync(packageListPath)) {
    console.log('Using old package-list.json structure...');
    
    try {
      const content = fs.readFileSync(packageListPath, 'utf-8');
      const packageList = JSON.parse(content);
      validateJsonFormatting(content);
      
      newPackages = getNewPackages(packageList);
    } catch (error) {
      throw new Error(`Failed to parse package-list.json: ${error.message}`);
    }
  }
  
  console.log('Validating packages:', newPackages.map(p => p.name).join(', '));

  for (const pkg of newPackages) {
    console.log(`\nValidating package: ${pkg.name}`);
    validateRequiredFields(pkg);
    validateRuntime(pkg);
    await validatePackagePublication(pkg);
    await validateEnvironmentVariables(pkg);
  }

  await provideFeedback(newPackages);
}

export function validateJsonFormatting(content) {
  const lines = content.split('\n');
  for (const line of lines) {
    if (line.trim() && line.match(/^( +)/)) {
      const indent = line.match(/^( +)/)[1].length;
      if (indent % 2 !== 0) {
        throw new Error(`Invalid indentation on line: ${line.trim()}\nUse 2 spaces for indentation.`);
      }
    }
  }

  const jsonWithoutComments = content.replace(/\/\/.*/g, '');
  const objects = jsonWithoutComments.match(/\{[^{}]*\}/g) || [];
  for (const obj of objects) {
    if (obj.match(/,[^\S\n]*[\]}]/)) {
      throw new Error('Remove trailing commas before closing brackets/braces');
    }
  }
}

function getNewPackages(packageList) {
  const baseBranch = 'main';
  const diffOutput = execSync(`git diff origin/${baseBranch} -- packages/package-list.json`).toString();
  const newPackages = [];

  // Extract complete JSON objects from diff
  const addedBlocks = diffOutput.match(/^\+\s*{[\s\S]*?^\+\s*}/gm) || [];

  for (const block of addedBlocks) {
    try {
      // Remove diff markers and normalize whitespace
      const cleanJson = block
        .split('\n')
        .map(line => line.replace(/^\+\s*/, ''))
        .join('\n');

      // Parse complete JSON object
      const pkg = JSON.parse(cleanJson);
      newPackages.push(pkg);
    } catch (error) {
      console.warn(`Warning: Failed to parse package block: ${error.message}`);
    }
  }

  return newPackages;
}

export function validateRequiredFields(pkg) {
  console.log('Checking required fields...');
  for (const field of REQUIRED_FIELDS) {
    if (!pkg[field]) {
      throw new Error(`Package ${pkg.name} is missing required field: ${field}`);
    }
  }

  console.log('Validating URLs...');
  const urlFields = ['sourceUrl', 'homepage'];
  for (const field of urlFields) {
    const url = pkg[field];
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      throw new Error(`Package ${pkg.name} has invalid ${field} URL: ${url} - must start with http:// or https://`);
    }
  }
}

export function validateRuntime(pkg) {
  console.log('Validating runtime...');
  if (!VALID_RUNTIMES.includes(pkg.runtime)) {
    throw new Error(`Package ${pkg.name} has invalid runtime: ${pkg.runtime}. Must be one of: ${VALID_RUNTIMES.join(', ')}`);
  }
}

async function validatePackagePublication(pkg) {
  const { name, runtime } = pkg;
  console.log(`Checking ${runtime} package publication...`);
  
  // Normalize the package name for npm/PyPI validation
  const normalizedName = normalizePackageName(name, runtime);
  console.log(`Normalized package name: ${normalizedName}`);

  if (runtime === 'node') {
    try {
      execSync(`npm view ${normalizedName} version`, { stdio: 'pipe' });
    } catch (error) {
      throw new Error(`Package ${name} (normalized as '${normalizedName}') is not published on npm. Please publish it first.`);
    }
  } else if (runtime === 'python') {
    try {
      const output = execSync(`pip install --dry-run ${normalizedName} 2>&1`, { encoding: 'utf-8' });
      console.log(`pip install output: ${output}`);
    } catch (error) {
      // Check if the error is due to Python version requirements
      if (error.stdout && error.stdout.includes('Ignored the following versions that require a different python version')) {
        console.log(`Package ${name} exists on PyPI but requires a different Python version. This is acceptable.`);
      } else {
        throw new Error(`Package ${name} (normalized as '${normalizedName}') is not published on PyPI. Please publish it first.`);
      }
    }
  } else if (runtime === 'go') {
    try {
      execSync(`go list ${normalizedName}`, { stdio: 'pipe' });
    } catch (error) {
      throw new Error(`Package ${name} (normalized as '${normalizedName}') is not a valid Go package. Please ensure it's a valid Go module.`);
    }
  }
}

async function validateEnvironmentVariables(pkg) {
  console.log('Validating environment variables...');
  
  // Check for environment variables in the package definition
  if (pkg.environmentVariables) {
    console.log('Found environment variables in package definition...');
    
    // Validate that all required variables have descriptions
    for (const [key, envVar] of Object.entries(pkg.environmentVariables)) {
      if (envVar.required && !envVar.description) {
        throw new Error(`Missing description for required environment variable '${key}' in package ${pkg.name}`);
      }
    }
  }
  
  // No environment variables needed for this package
  console.log('Environment variables validation passed');
}

async function provideFeedback(newPackages) {
  // Always skip GitHub API integration - just log the results
  console.log('\n--- PR Check Results ---');
  console.log(newPackages.length > 0
    ? `✅ Successfully validated ${newPackages.length} new package(s).`
    : '❌ No new packages found or validation failed.');
  console.log('------------------------\n');
  return;
}

validatePackages().catch(error => {
  console.error('\nValidation failed:', error.message);
  process.exit(1);
});
