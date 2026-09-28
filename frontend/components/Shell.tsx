"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
const sections=[["Home","/"],["Company Search","/search"],["Overview","overview"],["Fundamentals","fundamentals"],["Technical","technical"],["Announcements & Reports","announcements"],["Report Intelligence","report-intelligence"],["News","news"],["Thesis Scorecard","thesis"],["Catalyst Calendar","catalysts"],["Quant","quant"],["Forecasts","forecasts"],["Finance","finance"]];
export function Shell({children,ticker}:{children:React.ReactNode;ticker?:string}) {
 const path=usePathname();
 return <div className="shell"><aside className="sidebar"><Link href="/" className="brand">AXÍA<span>MARKET INTELLIGENCE</span></Link><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{sections.map(([name,route])=>{const href=route.startsWith("/")?route:ticker?`/company/${encodeURIComponent(ticker)}/${route}`:"/search";return <Link key={name} className={path===href?"nav active":"nav"} href={href}>{name}</Link>})}</nav><div className="sidebar-foot">All the evidence. A clearer perspective.</div></aside><div className="content"><header className="banner"><div><strong>AXÍA</strong><span>GLOBAL MARKET RESEARCH</span></div><Link href="/search" className="banner-search">Search companies →</Link></header><main>{children}</main><footer>AXÍA · Market Investment Analyst <span>Research information is not investment advice.</span></footer></div></div>;
}
