import ProductGrid from '../ProductGrid'
import nikeAirMax from "@assets/generated_images/Nike_Air_Max_sneakers_d0062d9e.png"
import adidasUltraBoost from "@assets/generated_images/Adidas_UltraBoost_shoes_d95acb11.png"

export default function ProductGridExample() {
  const mockProducts = [
    {
      id: "1",
      name: "Air Max 270",
      brand: "Nike",
      price: 150,
      image: nikeAirMax
    },
    {
      id: "2", 
      name: "UltraBoost 22",
      brand: "Adidas",
      price: 180,
      image: adidasUltraBoost
    }
  ]

  const handleAddToCart = (id: string) => {
    console.log('Added to cart:', id)
  }

  return (
    <div className="p-4">
      <ProductGrid products={mockProducts} onAddToCart={handleAddToCart} />
    </div>
  )
}