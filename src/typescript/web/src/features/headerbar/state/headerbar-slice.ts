
import { createSlice } from '@reduxjs/toolkit';
import { RootState } from '../../../store';

export const headerbarSlice = createSlice({
  name: 'headerbar',
  initialState: {
    "title": "Tornatura",
    "subtitle": ""
  },
  reducers: {
    setContentTitle: (state, action) => {
      const {title, subtitle} = action.payload;
      state.title = title;
      state.subtitle = subtitle;
    }
  },
});

export const headerbarSelectors = {
  selectTitle: (state: RootState) => state.headerbar.title,
};

export const headerbarActions = {
  setTitle: headerbarSlice.actions.setContentTitle,
};

export const headerbarReducer = headerbarSlice.reducer;