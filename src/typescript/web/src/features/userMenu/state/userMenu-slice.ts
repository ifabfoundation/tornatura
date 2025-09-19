import { createSlice } from "@reduxjs/toolkit";
import { RootState } from "../../../store";

const userMenuSlice = createSlice({
  name: "userMenu",
  initialState: { isOpen: false },
  reducers: {
    open: (state) => {
      state.isOpen = true;
    },
    close: (state) => {
      state.isOpen = false;
    },
    toggle: (state) => {
      state.isOpen = !state.isOpen;
    },
  },
});

export const userMenuSelectors = {
  selectIsOpen: (state: RootState) => state.userMenu.isOpen,
};

export const userMenuActions = {
  open: userMenuSlice.actions.open,
  close: userMenuSlice.actions.close,
  toggle: userMenuSlice.actions.toggle,
};

export const userMenuReducer = userMenuSlice.reducer;
