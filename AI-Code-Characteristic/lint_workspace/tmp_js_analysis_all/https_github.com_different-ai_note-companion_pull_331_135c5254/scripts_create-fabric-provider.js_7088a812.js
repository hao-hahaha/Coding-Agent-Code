const fs = require('fs');
const path = require('path');

// Content for the RCTThirdPartyFabricComponentsProvider.mm file
const providerContent = `/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#import "RCTThirdPartyFabricComponentsProvider.h"

namespace facebook {
namespace react {

void ThirdPartyFabricComponentsProvider::registerThirdPartyComponentsIfNeeded() {}

} // namespace react
} // namespace facebook`;

// Also create a header file if needed
const headerContent = `/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#pragma once

namespace facebook {
namespace react {

class ThirdPartyFabricComponentsProvider {
 public:
  static void registerThirdPartyComponentsIfNeeded();
};

} // namespace react
} // namespace facebook`;

// Try to find the React Native module in node_modules
function findReactNativePaths() {
  const basePaths = [
    process.cwd(),
    path.join(process.cwd(), '..'),
    path.join(process.cwd(), 'packages/mobile'),
    path.join(process.cwd(), '../packages/mobile')
  ];

  const foundPaths = [];
  
  for (const basePath of basePaths) {
    const rnPath = path.join(basePath, 'node_modules/react-native');
    if (fs.existsSync(rnPath)) {
      foundPaths.push(rnPath);
    }
  }

  return foundPaths;
}

// Also patch the cocoapods utils.rb file to add our method call
function patchCocoaPodsUtils(reactNativePath) {
  try {
    const utilsPath = path.join(reactNativePath, 'scripts/cocoapods/utils.rb');
    
    if (!fs.existsSync(utilsPath)) {
      console.log(`CocoaPods utils file not found at ${utilsPath}`);
      return false;
    }
    
    let content = fs.readFileSync(utilsPath, 'utf8');
    
    // Check if we need to add our fabric provider method
    if (!content.includes('ensure_fabric_provider_exists')) {
      // Add the method to the ReactNativePodsUtils class
      const fabricMethod = `
  # This method ensures the RCTThirdPartyFabricComponentsProvider.mm file exists
  # to prevent "Build input file cannot be found" errors
  def self.ensure_fabric_provider_exists()
    fabric_provider_path = File.join(File.dirname(__FILE__), "..", "..", "React", "Fabric", "RCTThirdPartyFabricComponentsProvider.mm")
    fabric_provider_header_path = File.join(File.dirname(__FILE__), "..", "..", "React", "Fabric", "RCTThirdPartyFabricComponentsProvider.h")
    
    unless File.exist?(fabric_provider_path)
      FileUtils.mkdir_p(File.dirname(fabric_provider_path))
      File.write(fabric_provider_path, "/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#import \\"RCTThirdPartyFabricComponentsProvider.h\\"

namespace facebook {
namespace react {

void ThirdPartyFabricComponentsProvider::registerThirdPartyComponentsIfNeeded() {}

} // namespace react
} // namespace facebook")
    end
    
    unless File.exist?(fabric_provider_header_path)
      FileUtils.mkdir_p(File.dirname(fabric_provider_header_path))
      File.write(fabric_provider_header_path, "/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#pragma once

namespace facebook {
namespace react {

class ThirdPartyFabricComponentsProvider {
 public:
  static void registerThirdPartyComponentsIfNeeded();
};

} // namespace react
} // namespace facebook")
    end
  end
`;
      
      // Insert after @@new_arch_enabled = false line
      content = content.replace(
        /@@new_arch_enabled = false\n/,
        `@@new_arch_enabled = false\n${fabricMethod}\n`
      );
      
      // Add a call to ensure_fabric_provider_exists before returning React params
      const returnParamsPattern = /return \{\n\s+:react_native_path => react_native_path,/;
      if (returnParamsPattern.test(content) && !content.includes('ensure_fabric_provider_exists()')) {
        content = content.replace(
          returnParamsPattern,
          `ensure_fabric_provider_exists()\n\n    return {\n      :react_native_path => react_native_path,`
        );
      }
      
      fs.writeFileSync(utilsPath, content);
      console.log(`Patched CocoaPods utils at ${utilsPath}`);
      return true;
    } else {
      console.log(`CocoaPods utils already patched at ${utilsPath}`);
      return true;
    }
  } catch (error) {
    console.error(`Error patching CocoaPods utils: ${error.message}`);
    return false;
  }
}

// Main function
function createFabricProvider() {
  // Find all possible React Native paths
  const reactNativePaths = findReactNativePaths();
  
  if (reactNativePaths.length === 0) {
    console.error('Could not find react-native module');
    return;
  }
  
  console.log(`Found React Native installations at: ${reactNativePaths.join(', ')}`);
  
  let success = false;
  
  // Process each React Native path found
  for (const reactNativePath of reactNativePaths) {
    try {
      const fabricDirPath = path.join(reactNativePath, 'React', 'Fabric');
      const fabricProviderPath = path.join(fabricDirPath, 'RCTThirdPartyFabricComponentsProvider.mm');
      const fabricHeaderPath = path.join(fabricDirPath, 'RCTThirdPartyFabricComponentsProvider.h');
      
      // Create the directory if it doesn't exist
      if (!fs.existsSync(fabricDirPath)) {
        fs.mkdirSync(fabricDirPath, { recursive: true });
      }
      
      // Create implementation file if needed
      if (!fs.existsSync(fabricProviderPath)) {
        fs.writeFileSync(fabricProviderPath, providerContent);
        console.log(`Created RCTThirdPartyFabricComponentsProvider.mm at ${fabricProviderPath}`);
      } else {
        console.log(`RCTThirdPartyFabricComponentsProvider.mm already exists at ${fabricProviderPath}`);
      }
      
      // Create header file if needed
      if (!fs.existsSync(fabricHeaderPath)) {
        fs.writeFileSync(fabricHeaderPath, headerContent);
        console.log(`Created RCTThirdPartyFabricComponentsProvider.h at ${fabricHeaderPath}`);
      } else {
        console.log(`RCTThirdPartyFabricComponentsProvider.h already exists at ${fabricHeaderPath}`);
      }
      
      // Patch CocoaPods utils.rb file
      if (patchCocoaPodsUtils(reactNativePath)) {
        success = true;
      }
    } catch (error) {
      console.error(`Error processing ${reactNativePath}: ${error.message}`);
    }
  }
  
  if (success) {
    console.log('Successfully fixed Fabric build issues!');
  } else {
    console.error('Failed to fix Fabric build issues');
  }
}

// Run the function
createFabricProvider();