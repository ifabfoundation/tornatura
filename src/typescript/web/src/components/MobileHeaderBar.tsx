import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../hooks";
import { SidebarActions } from "../features/sidebar/state/sidebar-slice";
import { headerbarSelectors } from "../features/headerbar/state/headerbar-slice";
import logoLeaf from "../assets/images/logo-leaf-color.svg";

function Hamburger() {
  const mobileOpen = useAppSelector((state) => state.sidebar.mobileOpen);
  return (
    <nav id="hamburger" className={mobileOpen ? "open" : ""}>
      <input type="checkbox" checked={mobileOpen} readOnly />
      <span></span>
      <span></span>
      <span></span>
    </nav>
  );
}

export default function MobileHeaderBar() {
  const dispatch = useAppDispatch();
  const mobileOpen = useAppSelector((state) => state.sidebar.mobileOpen);
  const navigate = useNavigate();
  const title = useAppSelector(headerbarSelectors.selectTitle);
  return (
    <div className="mobile-headerbar">
      <div className="logo-wrapper" onClick={() => navigate(`/`)}>
        <img src={logoLeaf} className="logo" alt="logo" />
      </div>
      <div className="title">{title}</div>
      <div
        className="hamburger-wrapper"
        onClick={() => dispatch(SidebarActions.setMenuMobileOpen(!mobileOpen))}
      >
        <Hamburger />
      </div>
    </div>
  );
}
