import type { Metadata } from "next";
import { canonical, siteUrl } from "../lib/seo";
import "./globals.css";
export const metadata: Metadata = {
 metadataBase: siteUrl,
 title:{default:"AXÍA | Global Market Research",template:"%s | AXÍA"},
 description:"Explore AXÍA's global market research workspace, financial evidence and investment-thesis monitoring.",
 alternates:{canonical:canonical("/")},
 openGraph:{type:"website",siteName:"AXÍA",title:"AXÍA | Global Market Research",description:"All the evidence. A clearer perspective.",url:canonical("/")},
 robots:{index:true,follow:true}
};
export default function RootLayout({children}:{children:React.ReactNode}) {
 const organization={"@context":"https://schema.org","@type":"Organization",name:"AXÍA",url:canonical("/")};
 const website={"@context":"https://schema.org","@type":"WebSite",name:"AXÍA",url:canonical("/"),description:"Global market research and evidence workspace"};
 return <html lang="en"><body><script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify([organization,website]).replace(/</g,"\\u003c")}}/>{children}</body></html>;
}
