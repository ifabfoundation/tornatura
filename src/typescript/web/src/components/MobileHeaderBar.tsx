interface MobileHeaderBarProps {
  setMobileOpen?: boolean;
  title?: string;
}

export default function MobileHeaderBar({
  setMobileOpen,
}: MobileHeaderBarProps) {
  return (
    <div className="mobile-headerbar">
      <div className="logo">LEAF</div>
      <div className="title"></div>
      <div className="hamburger" onClick={() => setMobileOpen(true)}>
        ====
      </div>
    </div>
  );
}
