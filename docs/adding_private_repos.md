# Adding private repositories

The selected tests project needs to be given access in order to access private repositories. This
access is granted via ssh keys. To give selected tests access to your repository, you will need
to add the selected tests public key as a deploy key in github. 

## Getting the public key

Ask the selected tests administrator for the public key.

## Adding the public key to your project

1. Go to repo settings in github

   ![Github settings](images/add_key_step_1.png)

2. Select the Deploy Keys section of settings

   ![Deploy Keys](images/add_key_step_2.png)

3. Select Add Key

   ![Add key](images/add_key_step_3.png)

4. Add the public key for selected tests

   ![Add public key](images/add_key_step_4.png)
