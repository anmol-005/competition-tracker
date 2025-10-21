# GitHub Pages Setup Instructions

## Quick Setup (5 minutes)

1. **Upload to GitHub:**
   - Create a new repository on GitHub
   - Upload all these files to your repository
   - Make sure the `docs/` folder is included

2. **Enable GitHub Pages:**
   - Go to your repository Settings
   - Scroll to "Pages" section
   - Set Source to "Deploy from a branch"
   - Select "main" branch and "/docs" folder
   - Click Save

3. **Access Your Site:**
   - Your site will be available at: `https://YOUR_USERNAME.github.io/REPOSITORY_NAME`
   - Initial deployment takes 2-3 minutes

## What's Included

```
📁 docs/                    # GitHub Pages deployment folder
├── index.html             # Main application file
├── assets/                # Optimized assets
│   ├── index-[hash].js    # Bundled JavaScript
│   ├── index-[hash].css   # Optimized CSS
│   └── *.png              # Shoe product images
└── README.md              # Project documentation

📁 .github/workflows/       # Automated deployment (optional)
└── deploy.yml             # Auto-deploy on push to main

📄 SETUP.md                # This file
```

## Features Working

✅ **Login Page** - Any email/password works  
✅ **Product Catalog** - 5 premium shoes displayed  
✅ **Add to Cart** - Real-time cart count updates  
✅ **Cart Page** - View cart contents and quantities  
✅ **Responsive Design** - Works on mobile and desktop  
✅ **Professional UI** - Clean, modern design  

## Manual Deployment

If you prefer manual deployment instead of GitHub Pages:

1. **For Netlify:** Drag the `docs/` folder to netlify.com/drop
2. **For Vercel:** Import the repo and set build output to `docs/`
3. **For Any Host:** Upload contents of `docs/` folder to web root

## Customization

To modify the store:
1. Edit the source files in the project
2. Run `npm run build` to regenerate the `docs/` folder
3. Commit changes to trigger auto-deployment

Your LabXpert - Store is now ready for the web! 🚀
