import ProductCard from '../ProductCard'
import nikeAirMax from "@assets/generated_images/Nike_Air_Max_sneakers_d0062d9e.png"

export default function ProductCardExample() {
  const handleAddToCart = (id: string) => {
    console.log('Added to cart:', id)
  }

  return (
    <div className="p-4 max-w-xs">
      <ProductCard 
        id="1"
        name="Air Max 270"
        brand="Nike"
        price={150}
        image={nikeAirMax}
        onAddToCart={handleAddToCart}
      />
    </div>
  )
}