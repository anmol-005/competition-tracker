import { MongoClient, Db, Collection } from 'mongodb';

// MongoDB Atlas connection
const MONGODB_URI = 'mongodb+srv://myUser:admin15@competitiontrackerclust.o8dxgmq.mongodb.net/?appName=CompetitiontrackerCluster';
const DATABASE_NAME = 'competition_tracker';

class MongoDBService {
  private client: MongoClient | null = null;
  private db: Db | null = null;

  async connect(): Promise<void> {
    if (this.client) {
      return; // Already connected
    }

    try {
      this.client = new MongoClient(MONGODB_URI);
      await this.client.connect();
      this.db = this.client.db(DATABASE_NAME);
      console.log('✅ Connected to MongoDB Atlas');
    } catch (error) {
      console.error('❌ MongoDB connection failed:', error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close();
      this.client = null;
      this.db = null;
      console.log('🔌 Disconnected from MongoDB');
    }
  }

  getDb(): Db {
    if (!this.db) {
      throw new Error('Database not connected. Call connect() first.');
    }
    return this.db;
  }

  getCollection(name: string): Collection {
    return this.getDb().collection(name);
  }

  // Get products in LabXpert format
  async getProducts(): Promise<any[]> {
    try {
      const productsCollection = this.getCollection('products');
      
      // Get ONLY catalog products (our main MacBook products) for now
      // Later we can add scraping data as additional products if needed
      const catalogProducts = await productsCollection.find({}).toArray();
      
      console.log(`📦 Found ${catalogProducts.length} catalog products`);
      
      // Transform MongoDB products to LabXpert format
      const transformedProducts = [];
      const seenASINs = new Set(); // Prevent duplicates
      
      // Transform catalog products (main MacBook products)
      for (const product of catalogProducts) {
        const transformed = await this.transformCatalogToLabXpertFormat(product);
        if (transformed && !seenASINs.has(transformed.ASIN)) {
          transformedProducts.push(transformed);
          seenASINs.add(transformed.ASIN);
        }
      }
      
      console.log(`� Loaded ${transformedProducts.length} products from database`);
      return transformedProducts;
      
    } catch (error) {
      console.error('❌ Error fetching products:', error);
      throw error;
    }
  }

  // Transform MongoDB product to LabXpert Product interface
  private async transformToLabXpertFormat(product: any): Promise<any | null> {
    try {
      // Extract product details
      const name = product.name || 'Unknown Product';
      const amazonData = product.platforms?.amazon;
      const smartprixData = product.platforms?.smartprix;
      const flipkartData = product.platforms?.flipkart;
      
      // Use Amazon data if available, otherwise Smartprix, then Flipkart
      const currentPrice = amazonData?.current_price || smartprixData?.current_price || flipkartData?.current_price || 0;
      
      // Extract model details from name
      const modelInfo = this.extractModelInfo(name);
      
      // Create proper ASIN - use existing ASIN or generate one based on model
      const asin = product.asin || this.generateSpecificASIN(modelInfo.modelName, modelInfo.color);
      
      return {
        ASIN: asin,
        Model_Name: modelInfo.modelName,
        Release_Year: modelInfo.year,
        RAM_GB: modelInfo.ram,
        Storage_GB: modelInfo.storage,
        Color: modelInfo.color,
        Base_Price: Math.round(currentPrice),
        image: amazonData?.url || smartprixData?.url || flipkartData?.url,
        // Add source info for debugging
        source: 'mongodb_products',
        original_name: name
      };
    } catch (error) {
      console.error('Error transforming product:', error);
      return null;
    }
  }

  // Transform Amazon scraping data to LabXpert format
  private async transformAmazonToLabXpertFormat(amazonProduct: any): Promise<any | null> {
    try {
      const title = amazonProduct.product_title || amazonProduct.title || 'Unknown Product';
      const price = this.parsePrice(amazonProduct.selling_price || amazonProduct.price_whole || '0');
      
      const modelInfo = this.extractModelInfo(title);
      
      return {
        ASIN: this.extractASIN(amazonProduct.product_link) || this.generateSpecificASIN(modelInfo.modelName, modelInfo.color),
        Model_Name: modelInfo.modelName,
        Release_Year: modelInfo.year,
        RAM_GB: modelInfo.ram,
        Storage_GB: modelInfo.storage,
        Color: modelInfo.color,
        Base_Price: price,
        image: amazonProduct.product_link,
        source: 'amazon_scraping_data',
        original_name: title
      };
    } catch (error) {
      console.error('Error transforming Amazon product:', error);
      return null;
    }
  }

  // Transform Flipkart reviews data to LabXpert format
  private async transformFlipkartToLabXpertFormat(flipkartProduct: any): Promise<any | null> {
    try {
      const name = flipkartProduct.product_name || flipkartProduct.name || 'Unknown Product';
      const price = this.parsePrice(flipkartProduct.price || flipkartProduct.current_price || '0');
      
      const modelInfo = this.extractModelInfo(name);
      
      return {
        ASIN: this.generateSpecificASIN(modelInfo.modelName, modelInfo.color),
        Model_Name: modelInfo.modelName,
        Release_Year: modelInfo.year,
        RAM_GB: modelInfo.ram,
        Storage_GB: modelInfo.storage,
        Color: modelInfo.color,
        Base_Price: price || 50000, // Default price if not available
        image: flipkartProduct.url || '',
        source: 'flipkart_reviews',
        original_name: name,
        // Additional Flipkart-specific data
        rating: flipkartProduct.average_rating || flipkartProduct.rating || 4.0,
        reviews_count: flipkartProduct.total_reviews || flipkartProduct.reviews?.length || 0
      };
    } catch (error) {
      console.error('Error transforming Flipkart product:', error);
      return null;
    }
  }

  // Transform catalog products (main MacBook products) to LabXpert format
  private async transformCatalogToLabXpertFormat(product: any): Promise<any | null> {
    try {
      // Handle both snake_case and PascalCase field names from stored products
      return {
        ASIN: product.ASIN || product.asin || product._id.toString(),
        Model_Name: product.Model_Name || product.model_name || product.product_title || 'Unknown Product',
        Release_Year: product.Release_Year || product.release_year || 2023,
        RAM_GB: product.RAM_GB || product.ram_gb || 8,
        Storage_GB: product.Storage_GB || product.storage_gb || 256,
        Color: product.Color || product.color || 'Silver',
        Base_Price: product.Base_Price || product.base_price || 0,
        image: product.image || '',
        source: 'catalog_products',
        original_name: product.product_title || product.model_name
      };
    } catch (error) {
      console.error('Error transforming catalog product:', error);
      return null;
    }
  }

  // Transform Smartprix scraping data to LabXpert format
  private async transformSmartprixToLabXpertFormat(smartprixProduct: any): Promise<any | null> {
    try {
      const title = smartprixProduct.product_title || 'Unknown Product';
      const price = this.parsePrice(smartprixProduct.price || '0');
      
      const modelInfo = this.extractModelInfo(title);
      
      return {
        ASIN: this.generateSpecificASIN(modelInfo.modelName, modelInfo.color),
        Model_Name: modelInfo.modelName,
        Release_Year: modelInfo.year,
        RAM_GB: modelInfo.ram,
        Storage_GB: modelInfo.storage,
        Color: modelInfo.color,
        Base_Price: price,
        image: smartprixProduct.product_link,
        source: 'smartprix_scraping_data',
        original_name: title,
        // Additional Smartprix-specific data
        user_score: smartprixProduct.user_score || 0,
        key_specs: smartprixProduct.key_specs || []
      };
    } catch (error) {
      console.error('Error transforming Smartprix product:', error);
      return null;
    }
  }

  // Extract model information from product name
  private extractModelInfo(name: string): any {
    const lowerName = name.toLowerCase();
    
    // Default values
    let modelName = 'MacBook';
    let year = 2023;
    let ram = 8;
    let storage = 256;
    let color = 'Silver';
    
    // Extract model name
    if (lowerName.includes('macbook air')) {
      modelName = 'MacBook Air';
      if (lowerName.includes('m1')) modelName += ' M1';
      else if (lowerName.includes('m2')) modelName += ' M2';
      else if (lowerName.includes('m3')) modelName += ' M3';
    } else if (lowerName.includes('macbook pro')) {
      modelName = 'MacBook Pro';
      if (lowerName.includes('m1')) modelName += ' M1';
      else if (lowerName.includes('m2')) modelName += ' M2';
      else if (lowerName.includes('m3')) {
        modelName += ' M3';
        if (lowerName.includes('m3 pro')) modelName += ' Pro';
        else if (lowerName.includes('m3 max')) modelName += ' Max';
      }
    } else if (lowerName.includes('iphone')) {
      modelName = 'iPhone';
      if (lowerName.includes('15')) modelName += ' 15';
      else if (lowerName.includes('14')) modelName += ' 14';
      else if (lowerName.includes('13')) modelName += ' 13';
      
      if (lowerName.includes('pro max')) modelName += ' Pro Max';
      else if (lowerName.includes('pro')) modelName += ' Pro';
      else if (lowerName.includes('plus')) modelName += ' Plus';
    } else if (lowerName.includes('samsung galaxy')) {
      modelName = 'Samsung Galaxy';
      if (lowerName.includes('s24')) modelName += ' S24';
      else if (lowerName.includes('s23')) modelName += ' S23';
      
      if (lowerName.includes('ultra')) modelName += ' Ultra';
      else if (lowerName.includes('plus')) modelName += ' Plus';
    }
    
    // Extract year
    const yearMatches = name.match(/20(1[8-9]|2[0-9])/);
    if (yearMatches) {
      year = parseInt(yearMatches[0]);
    } else {
      // Infer year from model
      if (lowerName.includes('m1')) year = 2020;
      else if (lowerName.includes('m2')) year = 2022;
      else if (lowerName.includes('m3')) year = 2023;
      else if (lowerName.includes('2024') || lowerName.includes('15')) year = 2024;
    }
    
    // Extract RAM
    const ramMatches = name.match(/(\d+)\s*gb\s*(unified\s*memory|ram|memory)/i);
    if (ramMatches) {
      ram = parseInt(ramMatches[1]);
    } else if (lowerName.includes('16gb') || lowerName.includes('16 gb')) {
      ram = 16;
    } else if (lowerName.includes('32gb') || lowerName.includes('32 gb')) {
      ram = 32;
    } else if (lowerName.includes('18gb') || lowerName.includes('18 gb')) {
      ram = 18;
    }
    
    // Extract storage
    const storageMatches = name.match(/(\d+)\s*(gb|tb)/i);
    if (storageMatches) {
      let storageValue = parseInt(storageMatches[1]);
      if (storageMatches[2].toLowerCase() === 'tb') {
        storageValue *= 1024; // Convert TB to GB
      }
      // Only set if it looks like storage (not RAM)
      if (storageValue >= 128) {
        storage = storageValue;
      }
    }
    
    // Extract color
    const colors = ['midnight', 'starlight', 'silver', 'space grey', 'space gray', 'space black', 'gold', 'rose gold', 'sky blue'];
    for (const colorOption of colors) {
      if (lowerName.includes(colorOption)) {
        color = colorOption.split(' ').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        break;
      }
    }
    
    return { modelName, year, ram, storage, color };
  }

  // Parse price from string
  private parsePrice(priceString: string): number {
    if (typeof priceString === 'number') return priceString;
    
    const cleanPrice = priceString.replace(/[₹,\s]/g, '');
    const price = parseFloat(cleanPrice);
    return isNaN(price) ? 0 : Math.round(price);
  }

  // Extract ASIN from Amazon URL
  private extractASIN(url: string): string | null {
    if (!url) return null;
    const asinMatch = url.match(/\/dp\/([A-Z0-9]{10})/);
    return asinMatch ? asinMatch[1] : null;
  }

  // Generate a random ASIN-like ID
  private generateASIN(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 10; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  // Generate specific ASIN based on model and color for consistent image mapping
  private generateSpecificASIN(modelName: string, color: string): string {
    // Known ASINs for existing images
    const knownMappings: Record<string, string> = {
      'MacBook Air M2_Midnight': 'B0B94152F6',
      'MacBook Air M2_Starlight': 'B0B94213G7', 
      'MacBook Pro M3_Space Grey': 'B0CJ5KWD22',
      'MacBook Pro M3 Pro_Space Black': 'B0CJ5LSM38',
      'MacBook Air M1_Silver': 'B08N5XSG8Z',
      // Add fallbacks for other models
      'iPhone 15 Pro Max_Natural Titanium': 'B0CHX1W1XY',
      'iPhone 15 Pro Max_Blue Titanium': 'B0CHX2PDLX',
      'Samsung Galaxy S24 Ultra_Titanium Black': 'B0CMDRCZBX',
      'Samsung Galaxy S24 Ultra_Titanium Gray': 'B0CMDQZPZX'
    };
    
    const key = `${modelName}_${color}`;
    if (knownMappings[key]) {
      return knownMappings[key];
    }
    
    // Generate consistent ASIN based on model name hash
    const hash = this.simpleHash(key);
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = 'B0';
    
    for (let i = 0; i < 8; i++) {
      result += chars.charAt((hash + i) % chars.length);
    }
    
    return result;
  }

  // Simple hash function for consistent ASIN generation
  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  // ===== USER AUTHENTICATION METHODS =====

  // Create a new user with username or email
  async createUser(identifier: string, password: string, role: string = 'user'): Promise<any> {
    try {
      const usersCollection = this.getCollection('users');
      
      // Determine if identifier is email or username
      const isEmail = identifier.includes('@');
      
      // Check if user already exists
      const existingUser = await usersCollection.findOne({ 
        $or: [
          { username: identifier },
          { email: identifier }
        ]
      });
      
      if (existingUser) {
        throw new Error(`${isEmail ? 'Email' : 'Username'} already exists`);
      }

      // Hash password
      const bcrypt = await import('bcrypt');
      const saltRounds = 12;
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // Create user document
      const newUser = {
        username: isEmail ? null : identifier,
        email: isEmail ? identifier : null,
        password: hashedPassword,
        role,
        created_at: new Date(),
        last_login: null,
        is_active: true
      };

      const result = await usersCollection.insertOne(newUser);
      
      console.log(`✅ User created: ${identifier} (${role})`);
      
      // Return user without password
      return {
        id: result.insertedId,
        username: newUser.username,
        email: newUser.email,
        role,
        created_at: newUser.created_at,
        is_active: newUser.is_active
      };
    } catch (error) {
      console.error('❌ Error creating user:', error);
      throw error;
    }
  }

  // Authenticate user with username or email
  async authenticateUser(identifier: string, password: string): Promise<any | null> {
    try {
      const usersCollection = this.getCollection('users');
      
      // Find user by username or email
      const user = await usersCollection.findOne({ 
        $or: [
          { username: identifier },
          { email: identifier }
        ],
        is_active: true
      });
      
      if (!user) {
        return null; // User not found
      }

      // Verify password
      const bcrypt = await import('bcrypt');
      const isValidPassword = await bcrypt.compare(password, user.password);
      
      if (!isValidPassword) {
        return null; // Invalid password  
      }

      // Update last login
      await usersCollection.updateOne(
        { _id: user._id },
        { $set: { last_login: new Date() } }
      );

      console.log(`✅ User authenticated: ${identifier}`);
      
      // Return user without password
      return {
        id: user._id,
        username: user.username,
        email: user.email,
        role: user.role,
        created_at: user.created_at,
        last_login: new Date(),
        is_active: user.is_active
      };
    } catch (error) {
      console.error('❌ Error authenticating user:', error);
      throw error;
    }
  }

  // Get user by username
  async getUserByUsername(username: string): Promise<any | null> {
    try {
      const usersCollection = this.getCollection('users');
      const user = await usersCollection.findOne({ username, is_active: true });
      
      if (!user) {
        return null;
      }

      // Return user without password
      return {
        id: user._id,
        username: user.username,
        role: user.role,
        created_at: user.created_at,
        last_login: user.last_login,
        is_active: user.is_active
      };
    } catch (error) {
      console.error('❌ Error authenticating user:', error);
      throw error;
    }
  }

  // Get all users (admin only)
  async getAllUsers(): Promise<any[]> {
    try {
      const usersCollection = this.getCollection('users');
      const users = await usersCollection.find({ is_active: true }).toArray();
      
      // Return users without passwords
      return users.map(user => ({
        id: user._id,
        username: user.username,
        email: user.email,
        role: user.role,
        created_at: user.created_at,
        last_login: user.last_login,
        is_active: user.is_active
      }));
    } catch (error) {
      console.error('❌ Error fetching all users:', error);
      throw error;
    }
  }

  // Create default admin account and other predefined users
  async createDefaultAdmin(): Promise<void> {
    try {
      const usersCollection = this.getCollection('users');
      
      // Define default users
      const defaultUsers = [
        { username: 'admin', password: 'admin123', role: 'admin' },
        { username: 'analyst', password: 'analyst123', role: 'analyst' },
        { username: 'viewer', password: 'viewer123', role: 'viewer' }
      ];

      let createdCount = 0;
      
      for (const user of defaultUsers) {
        // Check if user already exists
        const existingUser = await usersCollection.findOne({ username: user.username });
        if (!existingUser) {
          await this.createUser(user.username, user.password, user.role);
          console.log(`🔑 Default ${user.role} account created: ${user.username}/${user.password}`);
          createdCount++;
        } else {
          console.log(`ℹ️ ${user.role} account '${user.username}' already exists`);
        }
      }

      if (createdCount > 0) {
        console.log(`✅ Created ${createdCount} default user accounts`);
      } else {
        console.log('ℹ️ All default accounts already exist');
      }
      
    } catch (error) {
      console.error('❌ Error creating default users:', error);
    }
  }


}

// Export singleton instance
export const mongoService = new MongoDBService();