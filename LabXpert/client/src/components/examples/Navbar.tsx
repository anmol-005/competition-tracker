import Navbar from '../Navbar'

export default function NavbarExample() {
  const handleLogout = () => {
    console.log('Logout clicked')
  }

  return <Navbar isLoggedIn={true} onLogout={handleLogout} cartItemCount={3} />
}