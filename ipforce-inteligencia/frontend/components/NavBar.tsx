"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Phone, BarChart3, List, LogOut } from "lucide-react";

export default function NavBar() {
  const router = useRouter();
  function logout() {
    localStorage.removeItem("token");
    router.push("/login");
  }
  return (
    <nav className="border-b bg-background">
      <div className="flex h-16 items-center px-4 gap-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg">
          <Phone className="h-5 w-5" />
          IPForce
        </Link>
        <div className="flex-1" />
        <Link href="/dashboard">
          <Button variant="ghost" size="sm"><BarChart3 className="h-4 w-4 mr-2"/> Dashboard</Button>
        </Link>
        <Link href="/cdr">
          <Button variant="ghost" size="sm"><List className="h-4 w-4 mr-2"/> CDR</Button>
        </Link>
        <Button variant="ghost" size="sm" onClick={logout}><LogOut className="h-4 w-4 mr-2"/> Sair</Button>
      </div>
    </nav>
  );
}
