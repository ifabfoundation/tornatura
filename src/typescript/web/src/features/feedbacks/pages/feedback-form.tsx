import { useFormik } from "formik";
import React from "react";
import * as Yup from "yup";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { userSelectors } from "../../users/state/user-slice";
import { FeedbackCategoryEnum, FeedbackCreatePayload, FeedbacksApi } from "@tornatura/coreapis";
import { Alert } from "react-bootstrap";
import { getCoreApiConfiguration } from "../../../services/utils";

export function FeedbackForm() {
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const [message, setMessage] = React.useState<string>();
  const [hasError, setHasError] = React.useState<boolean>(false);

  const sendFeedback = async (feedback: FeedbackCreatePayload) => {
    const apiConfig = await getCoreApiConfiguration();
    const feedbackApi = new FeedbacksApi(apiConfig);
    const response = await feedbackApi.addFeedback(feedback);
    return response.data;
  };

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Invia Feedback", subtitle: "Subtitle" }));
  }, []);

  const formik = useFormik({
    initialValues: {
      category: FeedbackCategoryEnum.NewFeature,
      feedback: "",
    },
    validationSchema: Yup.object({
      feedback: Yup.string().required("Campo necessario"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const feedback: FeedbackCreatePayload = {
        category: values.category as FeedbackCategoryEnum,
        feedback: values.feedback,
        author: currentUser.id,
      };
      sendFeedback(feedback)
        .then((_) => {
          resetForm({});
          setSubmitting(false);
          setMessage("Feedback inviato con successo");
          setHasError(false);
        })
        .catch((_) => {
          setSubmitting(false);
          setMessage("Errore durante l'invio del feedback");
          setHasError(true);
        });
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      {message && (
        <Alert variant={hasError ? "danger" : "success"} dismissible>
          {message}
        </Alert>
      )}
      <div className="input-row">
        <label>
          Categoria
          <select
            id="category"
            name="category"
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.category}
          >
            <option value={FeedbackCategoryEnum.NewFeature}>Nuova funzionalita</option>
            <option value={FeedbackCategoryEnum.Improvement}>Miglioramento</option>
            <option value={FeedbackCategoryEnum.BugFixing}>Bug</option>
            <option value={FeedbackCategoryEnum.Other}>Altro</option>
          </select>
        </label>
      </div>
      <div className="input-row">
        <label>
          Feedback
          <textarea
            id="feedback"
            name="feedback"
            placeholder=""
            rows={15}
            cols={50}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            value={formik.values.feedback}
          ></textarea>
        </label>
        {formik.touched.feedback && formik.errors.feedback ? (
          <div className="error">{formik.errors.feedback}</div>
        ) : null}
      </div>
      <hr />
      <div className="buttons-wrapper">
        <input type="submit" className="primary" value="Invia" />
      </div>
    </form>
  );
}
