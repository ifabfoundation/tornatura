import { configureStore } from "@reduxjs/toolkit";
import { usersReducer } from "./features/users/state/user-slice";
import { headerbarReducer } from "./features/headerbar/state/headerbar-slice";
import { companiesReducer } from "./features/companies/state/companies-slice";
import { sidebarReducer } from "./features/sidebar/state/sidebar-slice";
import { feedbackReducer } from "./features/feedbacks/state/feedbacks-slice";
import { fieldsReducer } from "./features/fields/state/fields-slice";
import { detectionsReducer } from "./features/detections/state/detections-slice";

const store = configureStore({
  reducer: {
    companies: companiesReducer,
    headerbar: headerbarReducer,
    users: usersReducer,
    sidebar: sidebarReducer,
    feedbacks: feedbackReducer,
    fields: fieldsReducer,
    detections: detectionsReducer
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
