import Modal from "../../../components/Modal";
import { useFormik } from "formik";
import * as Yup from "yup";

interface DetectionUpdateModalFormProps {
  handleModalCancel: () => void;
  handleFormSubmitted: (data: { detectionTime: number }) => Promise<void>;
}

export function DetectionUpdateModalForm({
  handleModalCancel,
  handleFormSubmitted,
}: DetectionUpdateModalFormProps) {
  const formik = useFormik({
    initialValues: {
      detectionTime: "",
    },
    validationSchema: Yup.object({
      detectionTime: Yup.string().required("Specifica la data del rilevamento"),
    }),
    onSubmit: (values, { setSubmitting, resetForm }) => {
      const data = {
        detectionTime: new Date(values.detectionTime).getTime(),
      };
      handleFormSubmitted(data);
      resetForm({});
      setSubmitting(false);
    },
  });

  return (
    <Modal closeModal={handleModalCancel} title="Modifica Data Rilevamento">
      <section>
        <div className="mb-3"></div>
        <form onSubmit={formik.handleSubmit} autoComplete="off">
          <div className="input-row">
            <label>
              Data del rilevamento
              <input
                id="detectionTime"
                name="detectionTime"
                type="datetime-local"
                placeholder="Data rilevamento"
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                value={formik.values.detectionTime}
              />
            </label>
            {formik.touched.detectionTime && formik.errors.detectionTime ? (
              <div className="error">{formik.errors.detectionTime}</div>
            ) : null}
          </div>
          <hr />
          <div className="buttons-wrapper">
            <button className="trnt_btn secondary" onClick={handleModalCancel}>
              Cancel
            </button>
            <input type="submit" className="primary" value="Salva" disabled={formik.isSubmitting} />
          </div>
        </form>
      </section>
    </Modal>
  );
}
