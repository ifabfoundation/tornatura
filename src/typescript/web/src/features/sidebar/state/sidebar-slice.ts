import { createSlice } from "@reduxjs/toolkit";
import { RootState } from "../../../store";
import { MenuItemEntry } from "../../../components/Sidebar";

interface SidebarState {
  menuEntries: MenuItemEntry[];
  menuBottomEntries: MenuItemEntry[];
  mobileOpen: boolean;
}

const initialState: SidebarState = {
  menuEntries: [],
  menuBottomEntries: [],
  mobileOpen: false,
};

export const sidebarSlice = createSlice({
  name: "sidebar",
  initialState: initialState,
  reducers: {
    setMenuEntries: (state, action) => {
      state.menuEntries = action.payload;
    },
    setMenuBottomEntries: (state, action) => {
      state.menuBottomEntries = action.payload;
    },
    setMobileOpen: (state, action) => {
      state.mobileOpen = action.payload;
    },
  },
});

export const SidebarSelectors = {
  selectMenuEntries: (state: RootState) => state.sidebar,
};

export const SidebarActions = {
  setMenuEntriesAction: sidebarSlice.actions.setMenuEntries,
  setMenuBottomEntriesAction: sidebarSlice.actions.setMenuBottomEntries,
  setMenuMobileOpen: sidebarSlice.actions.setMobileOpen,
};

export const sidebarReducer = sidebarSlice.reducer;
