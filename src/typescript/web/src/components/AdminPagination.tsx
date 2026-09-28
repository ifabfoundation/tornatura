type AdminPaginationProps = {
  currentPage: number;
  pageSize: number;
  pageSizeOptions: number[];
  totalItems: number;
  disabled?: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

export function AdminPagination({
  currentPage,
  pageSize,
  pageSizeOptions,
  totalItems,
  disabled = false,
  onPageChange,
  onPageSizeChange,
}: AdminPaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const activePage = Math.min(currentPage, totalPages);
  const firstItem = totalItems === 0 ? 0 : (activePage - 1) * pageSize + 1;
  const lastItem = Math.min(activePage * pageSize, totalItems);

  return (
    <footer className="table-pagination" aria-label="Paginazione tabella">
      <span className="table-pagination__summary">
        {firstItem}–{lastItem} di {totalItems}
      </span>
      <div className="table-pagination__controls">
        <label>
          Righe
          <select
            value={pageSize}
            disabled={disabled}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          aria-label="Pagina precedente"
          disabled={disabled || activePage === 1}
          onClick={() => onPageChange(activePage - 1)}
        >
          ←
        </button>
        <span>Pagina {activePage} di {totalPages}</span>
        <button
          type="button"
          aria-label="Pagina successiva"
          disabled={disabled || activePage === totalPages}
          onClick={() => onPageChange(activePage + 1)}
        >
          →
        </button>
      </div>
    </footer>
  );
}
