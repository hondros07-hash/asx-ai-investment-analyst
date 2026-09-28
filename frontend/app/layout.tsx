import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title:{default:"AXÍA | Market Intelligence",template:"AXÍA | %s"},description:"AXÍA global investment research"};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>;}
