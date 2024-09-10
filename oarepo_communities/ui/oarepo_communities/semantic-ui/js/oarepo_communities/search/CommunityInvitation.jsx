import React from "react";
import { Modal, Button, Form, Icon, List } from "semantic-ui-react";
import { i18next } from "@translations/oarepo_communities";
import {
  useConfirmationModal,
  ArrayFieldItem,
  OARepoDepositSerializer,
  requiredMessage,
  returnGroupError,
  unique,
} from "@js/oarepo_ui";
import {
  ArrayField,
  TextField,
  RichInputField,
  http,
  ErrorLabel,
  FieldLabel,
} from "react-invenio-forms";
import { Formik, getIn } from "formik";
import PropTypes from "prop-types";
import * as Yup from "yup";

const memberInvitationsSchema = Yup.object().shape({
  members: Yup.array()
    .of(
      Yup.object().shape({
        email: Yup.string()
          .email("Invalid email format")
          .required(requiredMessage)
          .label(i18next.t("Email")),
        firstName: Yup.string().label(i18next.t("First name")),
        lastName: Yup.string().label(i18next.t("Last name")),
      })
    )
    .required(requiredMessage)
    .label(i18next.t("Members"))
    .test("unique-emails", returnGroupError, (value, context) =>
      unique(value, context, "email", i18next.t("Emails must be unique"))
    ),
  message: Yup.string().label(i18next.t("Message")),
  // role: Yup.string().required(requiredMessage).label(i18next.t("Role")),
});

export const CommunityInvitation = ({ rolesCanInvite, community }) => {
  const { isOpen, close, open } = useConfirmationModal();

  const onSubmit = async (values, formikBag) => {
    const serializer = new OARepoDepositSerializer([], ["__key"]);
    console.log(values);
    // Remove empty values and internal dependencies such as __key from array fields
    const serializedValues = serializer.serialize(values);
    serializedValues.members = serializedValues.members.map((m) => ({
      type: "email",
      id: m.email,
    }));
    console.log(serializedValues);

    await http.post(community.links.invitations, serializedValues);
  };
  const usersCanInvite = rolesCanInvite.user;
  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        members: [{ email: "", firstName: "", lastName: "" }],
        message: "",
        role: "member",
      }}
      validateOnChange={false}
      validateOnBlur={true}
      enableReinitialize={true}
      validationSchema={memberInvitationsSchema}
    >
      {({
        values,
        setFieldValue,
        setFieldTouched,
        handleSubmit,
        resetForm,
      }) => (
        <Modal
          className="form-modal"
          closeIcon
          open={isOpen}
          onClose={close}
          onOpen={open}
          trigger={
            <Button
              className="fluid-responsive"
              content={i18next.t("Invite...")}
              positive
              fluid
              compact
              icon="user plus"
              labelPosition="left"
              aria-expanded={isOpen}
              aria-haspopup="dialog"
            />
          }
        >
          <Modal.Header>
            {i18next.t("Invite users to the {{communityTitle}} community", {
              communityTitle: community.metadata.title,
            })}
          </Modal.Header>
          <Modal.Content>
            <Form>
              <ArrayField
                addButtonLabel={i18next.t("Add member")}
                fieldPath={"members"}
                addButtonClassName="array-field-add-button"
                defaultNewValue={{ email: "", firstName: "", lastName: "" }}
                label={<FieldLabel label={i18next.t("Members")} />}
              >
                {({ arrayHelpers, indexPath }) => {
                  const fieldPathPrefix = `members.${indexPath}`;
                  return (
                    <ArrayFieldItem
                      indexPath={indexPath}
                      arrayHelpers={arrayHelpers}
                      fieldPathPrefix={fieldPathPrefix}
                    >
                      <TextField
                        width={7}
                        fieldPath={`${fieldPathPrefix}.email`}
                        label={i18next.t("Email")}
                        required
                      />
                      <TextField
                        width={4}
                        fieldPath={`${fieldPathPrefix}.firstName`}
                        label={i18next.t("First name")}
                      />
                      <TextField
                        width={4}
                        fieldPath={`${fieldPathPrefix}.lastName`}
                        label={i18next.t("Last name")}
                      />
                    </ArrayFieldItem>
                  );
                }}
              </ArrayField>
              <Form.Field required className="rel-mt-1">
                <FieldLabel label={i18next.t("Role")} />
                <List selection>
                  {usersCanInvite.map((u) => (
                    <List.Item
                      key={u.name}
                      onClick={() => {
                        if (values.role === u.name) return;
                        setFieldValue("role", u.name);
                      }}
                      active={values.role === u.name}
                    >
                      <List.Content>
                        <List.Header>{u.title}</List.Header>
                        <List.Description>{u.description}</List.Description>
                      </List.Content>
                    </List.Item>
                  ))}
                </List>
                <ErrorLabel fieldPath="role" />
              </Form.Field>
              <RichInputField
                className="rel-mt-1"
                label={<FieldLabel label={i18next.t("Message")} />}
                fieldPath="message"
                optimized
                inputValue={() => getIn(values, "message", "")}
                initialValue=""
              />
            </Form>
          </Modal.Content>
          <Modal.Actions>
            <Button
              onClick={() => {
                close();
                resetForm();
              }}
              floated="left"
            >
              <Icon name="remove" /> {i18next.t("Cancel")}
            </Button>
            <Button
              primary
              onClick={handleSubmit}
              disabled={values.members.length === 0}
            >
              <Icon name="checkmark" /> {i18next.t("Invite")}
            </Button>
          </Modal.Actions>
        </Modal>
      )}
    </Formik>
  );
};

CommunityInvitation.propTypes = {
  rolesCanInvite: PropTypes.object.isRequired,
  community: PropTypes.object.isRequired,
};
