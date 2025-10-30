#!/usr/bin/env node

// Quick test script for LabXpert MongoDB integration
// Run this to test if the backend can connect to MongoDB and fetch products

import { mongoService } from './server/mongodb.js';

async function testMongoConnection() {
  console.log('🧪 Testing LabXpert MongoDB Integration');
  console.log('=' * 50);
  
  try {
    // Test connection
    console.log('🔌 Connecting to MongoDB Atlas...');
    await mongoService.connect();
    console.log('✅ Connected successfully!');
    
    // Test product fetching
    console.log('\n📦 Fetching products...');
    const products = await mongoService.getProducts();
    
    console.log(`✅ Found ${products.length} products`);
    
    // Display first few products
    console.log('\n📋 Sample Products:');
    products.slice(0, 5).forEach((product, index) => {
      console.log(`${index + 1}. ${product.Model_Name} (${product.Color})`);
      console.log(`   ASIN: ${product.ASIN}`);
      console.log(`   Price: ₹${product.Base_Price.toLocaleString()}`);
      console.log(`   RAM: ${product.RAM_GB}GB, Storage: ${product.Storage_GB}GB`);
      console.log(`   Year: ${product.Release_Year}`);
      if (product.source) console.log(`   Source: ${product.source}`);
      console.log('');
    });
    
    // Test product format
    console.log('📝 Product Structure Check:');
    if (products.length > 0) {
      const sampleProduct = products[0];
      const requiredFields = ['ASIN', 'Model_Name', 'Release_Year', 'RAM_GB', 'Storage_GB', 'Color', 'Base_Price'];
      
      requiredFields.forEach(field => {
        const hasField = sampleProduct.hasOwnProperty(field);
        console.log(`   ${field}: ${hasField ? '✅' : '❌'} ${hasField ? sampleProduct[field] : 'Missing'}`);
      });
    }
    
    await mongoService.disconnect();
    console.log('\n🎉 Test completed successfully!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error);
    process.exit(1);
  }
}

// Run the test
testMongoConnection();