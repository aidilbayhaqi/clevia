import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import ChatWidget from "./ChatWidget";
import { PublicDataProvider } from "../context/PublicDataContext";

export default function PublicLayout() {
  return <PublicDataProvider><div className="public-shell"><Navbar /><main><Outlet /></main><Footer /><ChatWidget /></div></PublicDataProvider>;
}
