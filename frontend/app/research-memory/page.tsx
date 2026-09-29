import type {Metadata} from "next";
import Link from "next/link";
import {Shell} from "../../components/Shell";
export const metadata:Metadata={title:"Research Memory",robots:{index:false,follow:false}};
export default function ResearchMemory(){
 return <Shell><div className="eyebrow">AXÍA / RESEARCH MEMORY</div><h1>Research Memory & What Changed</h1>
 <section className="panel"><h2>Historical research</h2><p>Research snapshots preserve dated observations and source information. Changes are compared only for the same security and currency.</p>
 <p>Authenticated research-history access is being integrated. This page does not expose account tokens or show another investor’s records.</p>
 <p className="method">The backend is feature-gated and disabled until database security, session integration and two-account isolation are verified.</p>
 <Link href="/search" className="button">Explore companies →</Link></section></Shell>;
}
