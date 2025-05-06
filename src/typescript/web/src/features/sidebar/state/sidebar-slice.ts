
import { createSlice } from '@reduxjs/toolkit';
import { RootState } from '../../../store';
import { MenuItemEntry } from '../../../components/Sidebar';


interface SidebarState {
  menuEntries: MenuItemEntry[];
  menuBottomEntries: MenuItemEntry[];
}

const initialState: SidebarState = {
  menuEntries: [],
  menuBottomEntries: []
};


export const sidebarSlice = createSlice({
  name: 'sidebar',
  initialState: initialState,
  reducers: {
    setMenuEntries: (state, action) => {
      state.menuEntries = action.payload;
    },
    setMenuBottomEntries: (state, action) => {
      state.menuBottomEntries = action.payload;
    }
  },
});

export const SidebarSelectors = {
  selectMenuEntries: (state: RootState) => state.sidebar,
};

export const SidebarActions = {
  setMenuEntriesAction: sidebarSlice.actions.setMenuEntries,
  setMenuBottomEntriesAction: sidebarSlice.actions.setMenuBottomEntries,
};

export const sidebarReducer = sidebarSlice.reducer;

